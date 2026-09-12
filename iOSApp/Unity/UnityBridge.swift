import Foundation
import UIKit

private let jcuUnityMessageCallback: @convention(c) (UnsafePointer<CChar>?) -> Void = { pointer in
    guard let pointer else { return }
    let json = String(cString: pointer)
    Task { @MainActor in
        CampusBridge.shared.receive(json: json)
    }
}

@MainActor
final class UnityBridge {
    static let shared = UnityBridge()

    private init() {
        JCUUnitySetMessageCallback(jcuUnityMessageCallback)
    }

    var isAvailable: Bool {
        JCUUnityIsAvailable()
    }

    func start() {
        JCUUnityStart()
    }

    func viewController() -> UIViewController? {
        JCUUnityViewController()
    }

    func show() {
        JCUUnityShow()
    }

    func unload() {
        JCUUnityUnload()
    }

    func send(json: String) {
        guard isAvailable else {
            print("[Stage A1][Swift→Unity host-only] \(json)")
            return
        }

        json.withCString { message in
            "CampusBridge".withCString { gameObject in
                "ReceiveFromNative".withCString { method in
                    JCUUnitySendMessage(gameObject, method, message)
                }
            }
        }
    }
}
