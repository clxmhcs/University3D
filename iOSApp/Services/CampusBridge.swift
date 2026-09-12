import Foundation

@MainActor
final class CampusBridge {
    static let shared = CampusBridge()
    static let protocolVersion = 1

    var onEvent: (@Sendable (UnityMessage) async -> Void)?

    private init() {}

    func focusObject(_ objectID: String) {
        send(UnityMessage(type: "focusObject", objectID: objectID))
    }

    func send(_ message: UnityMessage) {
        guard message.protocolVersion == Self.protocolVersion else {
            assertionFailure("CampusBridge protocol mismatch")
            return
        }

        do {
            let data = try JSONEncoder().encode(message)
            let json = String(decoding: data, as: UTF8.self)
            UnityBridge.shared.send(json: json)
        } catch {
            assertionFailure("Failed to encode UnityMessage: \(error)")
        }
    }

    func receive(json: String) {
        guard let data = json.data(using: .utf8) else { return }

        do {
            let message = try JSONDecoder().decode(UnityMessage.self, from: data)
            guard message.protocolVersion == Self.protocolVersion else {
                assertionFailure("CampusBridge protocol mismatch")
                return
            }

            if let onEvent {
                Task { await onEvent(message) }
            }
        } catch {
            assertionFailure("Failed to decode UnityMessage: \(error)")
        }
    }
}
