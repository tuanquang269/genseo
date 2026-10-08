// Subject lift (macOS Vision VNGenerateForegroundInstanceMaskRequest): real pack photo -> transparent PNG cutout.
// swift scripts/tools/subject_lift.swift <in> <out.png>   (used by scripts/landing_pack_shots.py)
import Foundation
import Vision
import CoreImage
import AppKit
let a = CommandLine.arguments
guard a.count == 3 else { print("usage: subject_lift <in> <out.png>"); exit(2) }
let url = URL(fileURLWithPath: a[1])
guard let ci = CIImage(contentsOf: url) else { print("cannot read"); exit(1) }
let req = VNGenerateForegroundInstanceMaskRequest()
let h = VNImageRequestHandler(ciImage: ci)
try h.perform([req])
guard let r = req.results?.first else { print("no subject"); exit(1) }
let buf = try r.generateMaskedImage(ofInstances: r.allInstances, from: h, croppedToInstancesExtent: true)
let out = CIImage(cvPixelBuffer: buf)
let ctx = CIContext()
try ctx.writePNGRepresentation(of: out, to: URL(fileURLWithPath: a[2]), format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
print("ok instances=\(r.allInstances.count) size=\(out.extent.size)")
