import SwiftUI

@main
struct University3DApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var environment = AppEnvironment()

    var body: some Scene {
        WindowGroup {
            CampusRootView()
                .environmentObject(environment)
        }
    }
}
