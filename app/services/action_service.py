from app.database.action_repository import ActionRepository
from app.models.action import Action


class ActionService:
    """
    Service métier du module Actions PMP.

    Assure la liaison entre l'interface utilisateur
    et ActionRepository.
    """

    def __init__(self):
        self.repository = ActionRepository()

    # ==========================================================
    # CREATE
    # ==========================================================

    def add_action(self, action: Action):
        """
        Ajoute une nouvelle action.
        """

        return self.repository.add(
            action
        )

    # ==========================================================
    # READ
    # ==========================================================

    def get_all(self):
        """
        Retourne toutes les actions enregistrées.
        """

        return self.repository.get_all()

    # ==========================================================
    # READ - ACTIONS EN COURS
    # ==========================================================

    def get_pending(self):
        """
        Retourne uniquement les actions non terminées.
        """

        return self.repository.get_pending()

    # ==========================================================
    # READ - ACTIONS IMPORTANTES À VENIR
    # ==========================================================

    def get_upcoming_important(self):
        """
        Retourne les actions importantes,
        non terminées et à venir.

        Utilisé notamment par le bloc
        "À surveiller" de l'accueil.
        """

        return (
            self.repository
            .get_upcoming_important()
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update_action(
        self,
        action: Action,
    ):
        """
        Modifie une action existante.
        """

        self.repository.update(
            action
        )

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete_action(
        self,
        action_id: int,
    ):
        """
        Supprime une action existante.
        """

        self.repository.delete(
            action_id
        )