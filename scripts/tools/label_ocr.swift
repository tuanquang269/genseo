// Read every text line in an image with macOS Vision (VNRecognizeTextRequest, accurate). Prints one line per
// observation: "<confidence>\t<text>". Used by scripts/landing_label_gate.py to reject generated packs whose label
// text is garbled (product-image-brandlock: never trust a label you did not read).
import Foundation
import Vision
import CoreImage
let a = CommandLine.arguments
guard a.count == 2, let ci = CIImage(contentsOf: URL(fileURLWithPath: a[1])) else { print("usage: label_ocr <img>"); exit(2) }
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false
req.minimumTextHeight = 0.008
try VNImageRequestHandler(ciImage: ci).perform([req])
for o in req.results ?? [] { if let c = o.topCandidates(1).first { print(String(format: "%.2f\t%@", c.confidence, c.string)) } }
