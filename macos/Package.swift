// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PersonalAssistant",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .executableTarget(
            name: "PersonalAssistant",
            path: "Sources"
        )
    ]
)
