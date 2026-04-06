import SwiftUI

@main
struct PersonalAssistantApp: App {
    var body: some Scene {
        MenuBarExtra("Personal Assistant", systemImage: "brain") {
            ContentView()
        }
        .menuBarExtraStyle(.window)
    }
}
