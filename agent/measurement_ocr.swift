import Foundation
import Vision
import ImageIO

guard CommandLine.arguments.count > 1 else { exit(2) }
let url = URL(fileURLWithPath: CommandLine.arguments[1])
guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { exit(3) }

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = ["en-GB", "en-US"]
try VNImageRequestHandler(cgImage: image).perform([request])
let rows = (request.results ?? []).compactMap { observation -> [String: Any]? in
    guard let candidate = observation.topCandidates(1).first else { return nil }
    let b = observation.boundingBox
    return ["text": candidate.string, "confidence": candidate.confidence,
            "box": [b.origin.x, b.origin.y, b.size.width, b.size.height]]
}
let data = try JSONSerialization.data(withJSONObject: rows)
FileHandle.standardOutput.write(data)
