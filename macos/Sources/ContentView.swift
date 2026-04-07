import SwiftUI

private enum CommandRoute {
    case process
    case organize
    case localHelp
}

private struct SlashCommand: Identifiable {
    let command: String
    let description: String
    let template: String
    let route: CommandRoute

    var id: String { command }
}

// MARK: - Type Badge

private struct TypeBadge: View {
    let type: String

    private var color: Color {
        switch type.lowercased() {
        case "task":  return .green
        case "note":  return .blue
        case "inbox": return .pink
        default:      return .secondary
        }
    }

    var body: some View {
        Text(type.uppercased())
            .font(.system(size: 9, weight: .bold, design: .rounded))
            .foregroundStyle(.white)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color, in: Capsule())
    }
}

// MARK: - Result Card

private struct ResultCard: View {
    let result: ProcessResponse

    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 10) {
                if result.duplicate {
                    Label("Já existe no Notion", systemImage: "exclamationmark.triangle")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.orange)

                    if let existing = result.existing {
                        Text(existing)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } else {
                    HStack(spacing: 6) {
                        if let type = result.type { TypeBadge(type: type) }
                        if let priority = result.priority {
                            Text(priority.uppercased())
                                .font(.system(size: 9, weight: .medium, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                    }
                    if let title = result.title {
                        Text(title)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(.primary)
                    }
                }

                if let urlString = result.notionUrl, let url = URL(string: urlString) {
                    Link(destination: url) {
                        Label("Abrir no Notion", systemImage: "arrow.up.right.square")
                            .font(.caption)
                    }
                }

                if let message = result.message, !message.isEmpty {
                    Text(message)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .transition(.move(edge: .bottom).combined(with: .opacity))
    }
}

// MARK: - Content View

struct ContentView: View {
    private let slashCommands: [SlashCommand] = [
        SlashCommand(
            command: "organize",
            description: "Prioriza tarefas do dia e ajusta status/ordem",
            template: "Organize minhas tarefas do dia por urgência, ajuste status e ordem sem criar tarefas novas.",
            route: .organize
        ),
        SlashCommand(
            command: "duvida",
            description: "Abrir modo de perguntas sobre produtividade",
            template: "Tenho uma dúvida: ",
            route: .process
        ),
        SlashCommand(
            command: "help",
            description: "Mostrar comandos disponíveis",
            template: "/help",
            route: .localHelp
        ),
    ]

    @State private var message = ""
    @State private var isLoading = false
    @State private var result: ProcessResponse?
    @State private var errorText: String?
    @FocusState private var inputFocused: Bool

    private var canSend: Bool {
        !message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isLoading
    }

    private var slashQuery: String? {
        let trimmed = message.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.hasPrefix("/") else { return nil }

        let token = trimmed.split(separator: " ", maxSplits: 1, omittingEmptySubsequences: true).first
        guard let token else { return "" }
        return token.replacingOccurrences(of: "/", with: "").lowercased()
    }

    private var commandSuggestions: [SlashCommand] {
        guard let slashQuery else { return [] }
        if slashQuery.isEmpty {
            return slashCommands
        }

        return slashCommands.filter { cmd in
            cmd.command.contains(slashQuery) || cmd.description.lowercased().contains(slashQuery)
        }
    }

    private var shouldShowCommands: Bool {
        inputFocused && !isLoading && slashQuery != nil
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("Personal Assistant", systemImage: "brain")
                .font(.headline)
                .foregroundStyle(.primary)

            TextField("Task, nota ou mensagem...", text: $message, axis: .vertical)
                .lineLimit(3...7)
                .textFieldStyle(.plain)
                .padding(10)
                .background(.quinary, in: RoundedRectangle(cornerRadius: 8))
                .focused($inputFocused)
                .onSubmit(submit)

            if shouldShowCommands {
                commandMenu
            }

            HStack {
                Text("Digite / para comandos · Return para enviar")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                Spacer()
                Button(action: submit) {
                    if isLoading {
                        ProgressView().scaleEffect(0.75)
                            .frame(width: 16, height: 16)
                    } else {
                        Text("Enviar")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(!canSend)
            }

            if let result {
                ResultCard(result: result)
            }

            if let errorText {
                Label(errorText, systemImage: "exclamationmark.circle")
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
        .padding(16)
        .frame(width: 340)
        .onAppear { inputFocused = true }
    }

    @ViewBuilder
    private var commandMenu: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 6) {
                if commandSuggestions.isEmpty {
                    Text("Nenhum comando encontrado")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(commandSuggestions) { command in
                        Button {
                            applyCommandTemplate(command)
                        } label: {
                            HStack(alignment: .firstTextBaseline, spacing: 8) {
                                Text("/\(command.command)")
                                    .font(.system(size: 12, weight: .semibold, design: .monospaced))
                                    .foregroundStyle(.primary)
                                Text(command.description)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.vertical, 2)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func applyCommandTemplate(_ command: SlashCommand) {
        if command.route == .localHelp {
            message = "/help"
            return
        }

        if command.route == .organize {
            message = "/\(command.command) \(command.template)"
            return
        }

        message = command.template
    }

    private func parseSlashCommand(_ text: String) -> (command: SlashCommand, args: String)? {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.hasPrefix("/") else { return nil }

        let parts = trimmed.split(separator: " ", maxSplits: 1, omittingEmptySubsequences: true)
        guard let rawCommand = parts.first else { return nil }

        let name = rawCommand.replacingOccurrences(of: "/", with: "").lowercased()
        guard let command = slashCommands.first(where: { $0.command == name }) else { return nil }

        let args = parts.count > 1 ? String(parts[1]).trimmingCharacters(in: .whitespacesAndNewlines) : ""
        return (command, args)
    }

    private func helpResponse() -> ProcessResponse {
        let helpText = """
        /organize: organiza tarefas existentes por urgência.
        /duvida: abre um prompt para perguntas.
        /help: mostra esta lista de comandos.
        """

        return ProcessResponse(
            duplicate: false,
            type: "note",
            title: "Comandos disponíveis",
            priority: nil,
            notionUrl: nil,
            message: helpText,
            existing: nil
        )
    }

    private func submit() {
        let trimmed = message.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        if let parsed = parseSlashCommand(trimmed) {
            if parsed.command.route == .localHelp {
                errorText = nil
                withAnimation(.easeOut(duration: 0.2)) {
                    result = helpResponse()
                }
                message = ""
                return
            }
        }

        isLoading = true
        errorText = nil
        result = nil

        Task {
            do {
                let response: ProcessResponse
                if let parsed = parseSlashCommand(trimmed) {
                    switch parsed.command.route {
                    case .organize:
                        let prompt = parsed.args.isEmpty ? parsed.command.template : parsed.args
                        response = try await APIService.shared.organizeTasks(message: prompt)
                    case .process:
                        let prompt = parsed.args.isEmpty ? parsed.command.template : parsed.args
                        response = try await APIService.shared.process(message: prompt)
                    case .localHelp:
                        response = helpResponse()
                    }
                } else {
                    response = try await APIService.shared.process(message: trimmed)
                }

                await MainActor.run {
                    withAnimation(.easeOut(duration: 0.2)) {
                        self.result = response
                        self.message = ""
                    }
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorText = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
}
