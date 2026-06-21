import Foundation
import Vision
import AppKit

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
let image = NSImage(contentsOf: url)!
var rect = NSRect(origin: .zero, size: image.size)
guard let cgImage = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
    fatalError("no cgImage")
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = ["te-IN", "sa-IN", "en-US"]
let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])
let obs = request.results as? [VNRecognizedTextObservation] ?? []
for o in obs.sorted(by: { $0.boundingBox.maxY > $1.boundingBox.maxY }) {
    if let cand = o.topCandidates(1).first {
        print(String(format:"%.3f %.3f %.3f %.3f | %@", o.boundingBox.minX, o.boundingBox.minY, o.boundingBox.width, o.boundingBox.height, cand.string))
    }
}
