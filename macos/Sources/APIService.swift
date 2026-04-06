import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case badResponse(Int)
    case decodingFailed(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "URL inválida."
        case .badResponse(let code):
            return "Resposta inesperada do servidor (código \(code))."
        case .decodingFailed(let error):
            return "Falha ao interpretar resposta: \(error.localizedDescription)"
        }
    }
}

actor APIService {
    static let shared = APIService()
    private let baseURL = "http://localhost:8000"

    func process(message: String) async throws -> ProcessResponse {
        guard let url = URL(string: "\(baseURL)/process") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(ProcessRequest(message: message))

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let http = response as? HTTPURLResponse else {
            throw APIError.badResponse(0)
        }
        guard http.statusCode == 200 else {
            throw APIError.badResponse(http.statusCode)
        }

        do {
            return try JSONDecoder().decode(ProcessResponse.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }
}
