import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class CategoryKind(str, enum.Enum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"
    AMBOS = "AMBOS"


class AccountType(str, enum.Enum):
    CONTA_CORRENTE = "CONTA_CORRENTE"
    CONTA_DIGITAL = "CONTA_DIGITAL"
    POUPANCA = "POUPANCA"
    DINHEIRO = "DINHEIRO"
    COFRINHO_RESERVA = "COFRINHO_RESERVA"
    INVESTIMENTO = "INVESTIMENTO"
    OUTROS = "OUTROS"


class TransactionType(str, enum.Enum):
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"
    TRANSFERENCIA = "TRANSFERENCIA"
    RENDIMENTO = "RENDIMENTO"
    AJUSTE = "AJUSTE"
    PAGAMENTO_FATURA = "PAGAMENTO_FATURA"
    PAGAMENTO_FINANCIAMENTO = "PAGAMENTO_FINANCIAMENTO"
    AMORTIZACAO = "AMORTIZACAO"


class TransactionStatus(str, enum.Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"


class InvoiceStatus(str, enum.Enum):
    ABERTA = "ABERTA"
    FECHADA = "FECHADA"
    PAGA = "PAGA"
    VENCIDA = "VENCIDA"


class CommitmentType(str, enum.Enum):
    FINANCIAMENTO = "FINANCIAMENTO"
    EMPRESTIMO = "EMPRESTIMO"
    CONSORCIO = "CONSORCIO"
    OUTROS = "OUTROS"


class CommitmentStatus(str, enum.Enum):
    ATIVO = "ATIVO"
    QUITADO = "QUITADO"
    CANCELADO = "CANCELADO"


class CommitmentInstallmentStatus(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PAGA = "PAGA"
    AMORTIZADA = "AMORTIZADA"
    CANCELADA = "CANCELADA"


class AmortizationType(str, enum.Enum):
    REDUCAO_PRAZO = "REDUCAO_PRAZO"
    REDUCAO_PARCELA = "REDUCAO_PARCELA"


class RecurrenceFrequency(str, enum.Enum):
    SEMANAL = "SEMANAL"
    MENSAL = "MENSAL"
    ANUAL = "ANUAL"
    PERSONALIZADA = "PERSONALIZADA"


class GoalStatus(str, enum.Enum):
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"
