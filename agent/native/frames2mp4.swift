// FRAMES TO MP4, using what the Mac already has.
//
// Draw Things hands a video model back over HTTP as a LIST OF PNG FRAMES; there is no
// movie file anywhere in that exchange. Something has to encode them, and the obvious
// something — ffmpeg — is not installed on this machine and would be a download plus a
// dependency for one job.
//
// AVFoundation is already here, and it encodes H.264 in an MP4 container with the
// hardware encoder. That matters beyond convenience: H.264/MP4 is the one format that
// plays in a <video> element, in Safari and Chrome alike, and in the Scene Study's
// THREE.VideoTexture with no negotiation at all. A WebM would have been a smaller
// change to make and a bigger one to live with.
//
//   frames2mp4 <out.mp4> <fps> <frame.png> [frame.png ...]
//
// Frames are appended in the order given. Exit 0 and print the path, or exit non-zero
// with the reason on stderr — the Python side turns that into a named failure.

import AVFoundation
import CoreGraphics
import Foundation
import ImageIO

func die(_ msg: String) -> Never {
    FileHandle.standardError.write(("frames2mp4: " + msg + "\n").data(using: .utf8)!)
    exit(2)
}

let args = Array(CommandLine.arguments.dropFirst())
guard args.count >= 3, let fps = Double(args[1]), fps > 0 else {
    die("usage: frames2mp4 <out.mp4> <fps> <frame.png> [...]")
}
let outPath = args[0]
let framePaths = Array(args.dropFirst(2))

// Decode the first frame to learn the size; every frame must match it, and a mismatch
// is reported rather than scaled, because a silent rescale would be a lie about what
// the model produced.
func loadCG(_ path: String) -> CGImage? {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil)
    else { return nil }
    return CGImageSourceCreateImageAtIndex(src, 0, nil)
}
guard let first = loadCG(framePaths[0]) else { die("could not decode \(framePaths[0])") }
// H.264 wants even dimensions.
let W = first.width - (first.width % 2)
let H = first.height - (first.height % 2)
guard W > 0, H > 0 else { die("first frame is \(first.width)x\(first.height)") }

// THE TIMESCALE HAS TO DIVIDE THE FRAME RATE EXACTLY, and 600 does not divide 16:
// 600/16 is 37.5, which rounded to 38 and made every clip 1.3% long — a 30-second cue
// landing 0.4s late against a timeline that is counting frames. 90000 is the MPEG
// timescale and it is 2^4 x 3^2 x 5^4, so it divides 8, 10, 12, 15, 16, 20, 24, 25, 30,
// 48, 50 and 60 without a remainder. A fractional rate still rounds, and the remainder
// is reported rather than hidden.
let scale: Int32 = 90000
let step = Int64((Double(scale) / fps).rounded())
if abs(Double(step) * fps - Double(scale)) > 0.001 {
    FileHandle.standardError.write(
        ("frames2mp4: note — \(fps) fps does not divide \(scale) exactly; "
         + "frame duration rounded to \(step)/\(scale)\n").data(using: .utf8)!)
}
let outURL = URL(fileURLWithPath: outPath)
try? FileManager.default.removeItem(at: outURL)

let writer: AVAssetWriter
do { writer = try AVAssetWriter(outputURL: outURL, fileType: .mp4) }
catch { die("could not open \(outPath) for writing: \(error.localizedDescription)") }

// ~0.1 bit per pixel per frame is generous for stage content, which is mostly bold
// flat-ish forms; the floor keeps small canvases from being starved.
let bitrate = max(2_000_000, Int(Double(W * H) * fps * 0.1))
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: W,
    AVVideoHeightKey: H,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: bitrate,
        AVVideoMaxKeyFrameIntervalKey: Int(fps.rounded()),
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
        AVVideoAllowFrameReorderingKey: false,
    ],
])
input.expectsMediaDataInRealTime = false
// AND THE TRACK HAS TO BE TOLD, not just the presentation times. Left alone the writer
// picks its own media timescale — 600 — and resamples every timestamp into it, which
// put 16 fps back to alternating 38/37 units. Setting it here is what makes a frame
// exactly one integer duration long.
input.mediaTimeScale = scale
let adaptor = AVAssetWriterInputPixelBufferAdaptor(
    assetWriterInput: input,
    sourcePixelBufferAttributes: [
        kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA),
        kCVPixelBufferWidthKey as String: W,
        kCVPixelBufferHeightKey as String: H,
    ])
guard writer.canAdd(input) else { die("AVAssetWriter refused an H.264 \(W)x\(H) input") }
writer.add(input)
guard writer.startWriting() else {
    die("AVAssetWriter would not start: \(writer.error?.localizedDescription ?? "no reason given")")
}
writer.startSession(atSourceTime: .zero)

var index: Int64 = 0

func pixelBuffer(_ img: CGImage) -> CVPixelBuffer? {
    var pb: CVPixelBuffer?
    let attrs: [String: Any] = [kCVPixelBufferCGImageCompatibilityKey as String: true,
                                kCVPixelBufferCGBitmapContextCompatibilityKey as String: true]
    guard CVPixelBufferCreate(kCFAllocatorDefault, W, H, kCVPixelFormatType_32BGRA,
                              attrs as CFDictionary, &pb) == kCVReturnSuccess,
          let buf = pb else { return nil }
    CVPixelBufferLockBaseAddress(buf, [])
    defer { CVPixelBufferUnlockBaseAddress(buf, []) }
    guard let ctx = CGContext(data: CVPixelBufferGetBaseAddress(buf),
                              width: W, height: H, bitsPerComponent: 8,
                              bytesPerRow: CVPixelBufferGetBytesPerRow(buf),
                              space: CGColorSpaceCreateDeviceRGB(),
                              bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
                                  | CGBitmapInfo.byteOrder32Little.rawValue)
    else { return nil }
    // Drawn into the exact output rect: a frame that is a pixel or two off (the even
    // dimension crop above) is filled rather than left as uninitialised memory.
    ctx.draw(img, in: CGRect(x: 0, y: 0, width: W, height: H))
    return buf
}

for path in framePaths {
    guard let img = loadCG(path) else { die("could not decode \(path)") }
    guard let buf = pixelBuffer(img) else { die("could not make a \(W)x\(H) pixel buffer") }
    // The writer pulls; spinning here is correct for a non-real-time encode and this
    // never runs unbounded because the input drains on its own thread.
    while !input.isReadyForMoreMediaData { usleep(2000) }
    guard adaptor.append(buf, withPresentationTime: CMTime(value: index * step, timescale: scale))
    else { die("frame \(index) was refused: \(writer.error?.localizedDescription ?? "no reason given")") }
    index += 1
}

input.markAsFinished()
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()

if writer.status != .completed {
    die("the movie did not finish: \(writer.error?.localizedDescription ?? "no reason given")")
}
print(outPath)
