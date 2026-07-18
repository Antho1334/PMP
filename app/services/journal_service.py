from datetime import date

from app.database.activity_repository import ActivityRepository
from app.models.activity import Activity


class JournalService:
    """
    Service métier du Journal PMP.

    Assure la liaison entre l'interface utilisateur
    et ActivityRepository.
    """

    def __init__(self):
        self.repository = ActivityRepository()

    # ==========================================================
    # CREATE
    # ==========================================================

    def add_activity(self, activity: Activity):
        """
        Ajoute une nouvelle activité au Journal.
        """

        return self.repository.add(activity)

    # ==========================================================
    # READ
    # ==========================================================

    def get_all(self):
        """
        Retourne toutes les activités enregistrées.
        """

        return self.repository.get_all()

    # ==========================================================
    # SEARCH BY KEYWORD
    # ==========================================================

    def search_activities(self, keyword: str):
        """
        Recherche des activités à partir d'un mot-clé.

        La recherche porte sur :
        - la catégorie ;
        - l'objet ;
        - le compte-rendu.
        """

        return self.repository.search(keyword)

    # ==========================================================
    # SEARCH BY DATE
    # ==========================================================

    def search_activities_by_date(self, activity_date: date):
        """
        Recherche toutes les activités enregistrées
        pour une date précise.
        """

        return self.repository.search_by_date(
            activity_date
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update_activity(self, activity: Activity):
        """
        Modifie une activité existante.
        """

        self.repository.update(activity)

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete_activity(self, activity_id: int):
        """
        Supprime une activité existante à partir de son ID.
        """

        self.repository.delete(activity_id)

    # ==========================================================
    # DELETE ALL
    # ==========================================================

    def clear(self):
        """
        Supprime toutes les activités du Journal.

        Conservé pour compatibilité.
        """

        self.repository.delete_all()