import Foundation

@MainActor
final class UnityBridge {
    static let shared = UnityBridge()

    private init() {}

    func send(json: String) {
        #if canImport(UnityFramework)
        // Stage A integration point:
        // Forward `json` to the Unity GameObject named "CampusBridge"
        // method: ReceiveFromNative
        //
        // Keep this wrapper as the only Swift-side entry point into Unity.
        UnityRuntimeAdapter.shared.sendToUnity(
            gameObject: "CampusBridge",
            method: "ReceiveFromNative",
            message: json
        )
        #else
        print("[Stage A][Swift→Unity placeholder] \(json)")
        #endif
    }
}

#if canImport(UnityFramework)
import UnityFramework

@MainActor
final class UnityRuntimeAdapter {
    static let shared = UnityRuntimeAdapter()

    private init() {}

    func sendToUnity(gameObject: String, method: String, message: String) {
        // The concrete UnityFramework lifecycle is wired after the Unity iOS export
        // is added to the Xcode workspace. No business logic belongs here.
        UnitySendMessage(gameObject, method, message)
    }
}
#endif
