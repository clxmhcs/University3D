import SwiftUI

@main
struct University3DApp: App {
    @StateObject private var environment = AppEnvironment()

    var body: some Scene {
        WindowGroup {
            CampusRootView()
                .environmentObject(environment)
        }
    }
}
