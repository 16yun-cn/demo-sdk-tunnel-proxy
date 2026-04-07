// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "SwiftAlamofireTunnelPackage",
    products: [
        .executable(name: "main", targets: ["TunnelDemoApp"])
    ],
    dependencies: [
        .package(name: "AlamofirePackage", url: "https://github.com/Alamofire/Alamofire.git", from: "5.8.0")
    ],
    targets: [
        .executableTarget(
            name: "TunnelDemoApp",
            dependencies: [
                .product(name: "Alamofire", package: "AlamofirePackage")
            ],
            path: "Sources"
        )
    ]
)
