"""Registre des sources participant au bilan quotidien."""

from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata


class DailyReportRegistry:
    """Maintient la collection ordonnée des providers de bilan."""

    def __init__(self) -> None:
        self._providers: list[DailyReportProvider] = []

    def register(self, provider: DailyReportProvider) -> None:
        """Enregistre un provider dont le nom n'est pas déjà présent."""

        if not isinstance(provider, DailyReportProvider):
            raise TypeError("provider doit être un DailyReportProvider.")
        metadata = provider.metadata
        if not isinstance(metadata, ProviderMetadata):
            raise TypeError("provider.metadata doit être un ProviderMetadata.")
        if any(current.metadata.name == metadata.name for current in self._providers):
            raise ValueError(f"Un provider nommé {metadata.name!r} est déjà enregistré.")
        self._providers.append(provider)

    def unregister(self, provider_name: str) -> None:
        """Retire le provider identifié par son nom stable."""

        if not isinstance(provider_name, str):
            raise TypeError("provider_name doit être une chaîne de caractères.")
        if not provider_name.strip():
            raise ValueError("provider_name ne peut pas être vide.")
        for index, provider in enumerate(self._providers):
            if provider.metadata.name == provider_name:
                del self._providers[index]
                return
        raise KeyError(provider_name)

    def clear(self) -> None:
        """Retire tous les providers enregistrés."""

        self._providers.clear()

    @property
    def providers(self) -> tuple[DailyReportProvider, ...]:
        """Expose un instantané immuable des providers."""

        return tuple(self._providers)

    @property
    def provider_count(self) -> int:
        """Retourne le nombre de providers enregistrés."""

        return len(self._providers)
