// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "SwiftURLSessionTunnelDemo",
    products: [
        .executable(name: "main", targets: ["SwiftURLSessionTunnelDemo"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "SwiftURLSessionTunnelDemo",
            dependencies: [],
            path: "Sources"
        )
    ]
)
