import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

func readPNG(_ path: String) -> CGImage {
    let url = URL(fileURLWithPath: path)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fatalError("Unable to read \(path)")
    }
    return image
}

let shield = readPNG("icons/source/shield.png")
let cookieCloud = readPNG("icons/source/cookiecloud.png")
let size = 512
guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
      let canvas = CGContext(data: nil, width: size, height: size, bitsPerComponent: 8,
                             bytesPerRow: 0, space: colorSpace,
                             bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
    fatalError("Unable to create canvas")
}
canvas.interpolationQuality = .high
canvas.draw(shield, in: CGRect(x: 0, y: 0, width: size, height: size))
// Scale and place the original CookieCloud artwork as a separate layer.
canvas.draw(cookieCloud, in: CGRect(x: 159, y: 228, width: 194, height: 194))

let output = URL(fileURLWithPath: "icons/cookieclouddeleteguard.png")
guard let image = canvas.makeImage(),
      let destination = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil) else {
    fatalError("Unable to create PNG")
}
CGImageDestinationAddImage(destination, image, nil)
guard CGImageDestinationFinalize(destination) else { fatalError("Unable to write PNG") }
