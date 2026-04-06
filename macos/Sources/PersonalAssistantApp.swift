import SwiftUI

@main
struct PersonalAssistantApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        // UI é gerenciada pelo AppDelegate via NSStatusItem + NSPopover
        Settings { EmptyView() }
    }
}
