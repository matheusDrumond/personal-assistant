import Foundation

struct ProcessRequest: Encodable {
    let message: String
}

struct ProcessResponse: Decodable {
    let duplicate: Bool
    let type: String?
    let title: String?
    let priority: String?
    let notionUrl: String?
    let message: String?
    let existing: String?

    enum CodingKeys: String, CodingKey {
        case duplicate
        case type
        case title
        case priority
        case notionUrl = "notion_url"
        case message
        case existing
    }
}
