"""FinOps pricing baselines, renewal window types, and quota diagnostic rules."""

from dataclasses import dataclass
from typing import Literal

# Commercial reference pricing baseline: OpenAI GPT-4o ($/token)
# Benchmark against which free-tier monetary savings are quantified.
GPT4O_INPUT_COST_PER_TOKEN: float = 2.50 / 1_000_000
GPT4O_OUTPUT_COST_PER_TOKEN: float = 10.00 / 1_000_000

RenewalType = Literal[
    "sliding_window_1m",
    "rolling_daily_24h",
    "monthly_credits",
    "quota_static_tier",
]


@dataclass(frozen=True, slots=True)
class ProviderRenewalMeta:
    """Metadata describing the quota reset window and renewal behavior of an LLM provider."""

    provider_name: str
    display_name: str
    renewal_type: RenewalType
    renewal_window_label: str
    free_tier_limits_label: str
    is_auto_renewable: bool
    description: str


PROVIDER_RENEWAL_REGISTRY: dict[str, ProviderRenewalMeta] = {
    "groq": ProviderRenewalMeta(
        provider_name="groq",
        display_name="Groq Cloud LPU",
        renewal_type="sliding_window_1m",
        renewal_window_label="Fenêtre glissante 60s (TPM/RPM)",
        free_tier_limits_label="6 000 TPM / 30 RPM / 14 400 RPD",
        is_auto_renewable=True,
        description="Plafond réinitialisé en continu chaque minute. En cas de 429, patienter 60s.",
    ),
    "sambanova": ProviderRenewalMeta(
        provider_name="sambanova",
        display_name="SambaNova Systems SN40L",
        renewal_type="sliding_window_1m",
        renewal_window_label="Fenêtre glissante 60s",
        free_tier_limits_label="Débit pétaflopique chips RDU",
        is_auto_renewable=True,
        description="Accélération matérielle RDU avec réinitialisation par minute.",
    ),
    "google": ProviderRenewalMeta(
        provider_name="google",
        display_name="Google AI Studio / Gemini",
        renewal_type="rolling_daily_24h",
        renewal_window_label="Quotidien (00:00 UTC)",
        free_tier_limits_label="1 500 RPD / 15 RPM / 1M TPM",
        is_auto_renewable=True,
        description="Quota généreux de 1 500 requêtes réinitialisé chaque nuit à minuit UTC.",
    ),
    "cloudflare": ProviderRenewalMeta(
        provider_name="cloudflare",
        display_name="Cloudflare Workers AI",
        renewal_type="rolling_daily_24h",
        renewal_window_label="Quotidien (00:00 UTC)",
        free_tier_limits_label="10 000 neurones / jour",
        is_auto_renewable=True,
        description="Quota journalier de calculs neuronaux réinitialisé à minuit UTC.",
    ),
    "openrouter": ProviderRenewalMeta(
        provider_name="openrouter",
        display_name="OpenRouter Distributed Network",
        renewal_type="rolling_daily_24h",
        renewal_window_label="Quotidien (00:00 UTC)",
        free_tier_limits_label="20 à 200 RPD (selon modèle :free)",
        is_auto_renewable=True,
        description="Modèles gratuits avec allocations quotidiennes réinitialisées chaque jour.",
    ),
    "cohere": ProviderRenewalMeta(
        provider_name="cohere",
        display_name="Cohere Platform",
        renewal_type="monthly_credits",
        renewal_window_label="Mensuel (1er du mois)",
        free_tier_limits_label="1 000 appels / mois (Trial)",
        is_auto_renewable=True,
        description="Allocation d'essai mensuelle réinitialisée au 1er jour de chaque mois.",
    ),
    "zai": ProviderRenewalMeta(
        provider_name="zai",
        display_name="z.ai / Zhipu AI",
        renewal_type="quota_static_tier",
        renewal_window_label="Quota de crédits / Journalier",
        free_tier_limits_label="Crédits d'amorçage gratuits",
        is_auto_renewable=False,
        description="Solde de démarrage ou jetons de subvention nécessitant recharge manuelle.",
    ),
    "meta": ProviderRenewalMeta(
        provider_name="meta",
        display_name="Meta AI Direct Llama",
        renewal_type="sliding_window_1m",
        renewal_window_label="Fenêtre glissante 60s",
        free_tier_limits_label="Taux variables",
        is_auto_renewable=True,
        description="Inférence directe Llama via gateway.",
    ),
    "kimi": ProviderRenewalMeta(
        provider_name="kimi",
        display_name="Kimi / Moonshot AI",
        renewal_type="quota_static_tier",
        renewal_window_label="Crédits / Par jeton",
        free_tier_limits_label="Crédits initiaux",
        is_auto_renewable=False,
        description="Solde de découverte nécessitant approvisionnement une fois épuisé.",
    ),
    "novita": ProviderRenewalMeta(
        provider_name="novita",
        display_name="Novita AI Cluster",
        renewal_type="quota_static_tier",
        renewal_window_label="Crédits / Par jeton",
        free_tier_limits_label="Solde d'essai (Trial Balance)",
        is_auto_renewable=False,
        description="Solde d'essai ; bascule en 403 si le solde est nul sans carte enregistrée.",
    ),
}


def calculate_savings_usd(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate comparative savings in USD against the commercial GPT-4o baseline."""
    return round(
        (prompt_tokens * GPT4O_INPUT_COST_PER_TOKEN)
        + (completion_tokens * GPT4O_OUTPUT_COST_PER_TOKEN),
        6,
    )


def get_provider_renewal_meta(provider_name: str) -> ProviderRenewalMeta:
    """Retrieve metadata describing renewal cycles for a provider."""
    p = provider_name.strip().lower()
    return PROVIDER_RENEWAL_REGISTRY.get(
        p,
        ProviderRenewalMeta(
            provider_name=p,
            display_name=p.capitalize(),
            renewal_type="quota_static_tier",
            renewal_window_label="Inconnu / Statique",
            free_tier_limits_label="Non documenté",
            is_auto_renewable=False,
            description="Fournisseur générique ou non répertorié.",
        ),
    )
