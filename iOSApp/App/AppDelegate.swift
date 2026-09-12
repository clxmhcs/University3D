import UIKit

final class AppDelegate: NSObject, UIApplicationDelegate {
    func applicationWillTerminate(_ application: UIApplication) {
        Task { @MainActor in
            UnityBridge.shared.unload()
        }
    }
}
