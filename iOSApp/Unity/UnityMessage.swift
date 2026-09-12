import Foundation

struct UnityMessage: Codable, Equatable {
    let protocolVersion: Int
    let type: String
    let objectID: String?
    let payload: [String: String]?

    init(
        protocolVersion: Int = 1,
        type: String,
        objectID: String? = nil,
        payload: [String: String]? = nil
    ) {
        self.protocolVersion = protocolVersion
        self.type = type
        self.objectID = objectID
        self.payload = payload
    }
}
