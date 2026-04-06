import SwiftUI

@main
struct PersonalAssistantApp: App {
    var body: some Scene {
        WindowGroup("Personal Assistant") {
            ContentView()
        }
        .windowResizability(.contentMinSize)
        .commands {
            // Remove "New Window" da barra de menus (não faz sentido para este app)
            CommandGroup(replacing: .newItem) {}
        }
    }
}
