import os
import sys
from build_teacher_classeur import build_teacher_classeur

# 1. Config Aziza Jouaidi
config_aziza = {
    'key': 'AZIZA',
    'name_upper': 'Mme AZIZA JOUAIDI',
    'name_title': 'Mme Aziza Jouaidi',
    'specialite': 'Comportements professionnels, Procédures pré-départ & Secourisme',
    'out_docx': r"D:\Piopi\Cahier text\Planning année 2026-2028\Classeur formateur\Classeur-Pédagogique-Formateur-Aziza Jouaidi.docx",
    'modules': [
        ("01", "Métier et Formation", "30", "M1"),
        ("04", "Environnement professionnel", "180", "M4"),
        ("05", "Comportement et attitudes professionnels", "60", "M5"),
        ("11", "PROCÉDURES DE PRÉ-DÉPART", "60", "M11"),
        ("14", "Secourisme", "165", "M14")
    ],
    'weekly_slots': [
        ("Lundi", "ATAM - 1ère Année M4 (09h-11h / 11h-13h) (ou M1/M11 : 09h-12h)", "ATAM - 1ère Année M5 (13h-16h) (ou M11 : 13h-16h)", "—"),
        ("Mardi", "ATAM - 1ère Année M4 (09h-11h / 11h-13h) (ou M1/M11 : 09h-12h)", "ATAM - 1ère Année M5 (13h-16h) (ou M11 : 13h-16h)", "—"),
        ("Mercredi", "ATAM - 1ère Année M4 (09h-11h / 11h-13h) (ou M1/M11 : 09h-12h)", "ATAM - 1ère Année M5 (13h-16h) (ou M11 : 13h-16h)", "—"),
        ("Jeudi", "ATAM - 1ère Année M4 (09h-11h / 11h-13h) (ou M1/M11 : 09h-12h)", "ATAM - 1ère Année M5 (13h-16h) (ou M11 : 13h-16h)", "—"),
        ("Vendredi", "ATAM - 1ère Année M4 (09h-11h / 11h-13h) (ou M1/M11 : 09h-12h)", "ATAM - 1ère Année M5 (13h-16h) (ou M11 : 13h-16h)", "—"),
        ("Samedi", "—", "—", "ATAM - 1ère & 2ème Année : Contrôles Continus (C.C) & Épreuves Sommatives (M5 / M11 / M4 / M14)")
    ],
    'gantt1_highlight': ["M1", "M4", "M5", "M11"],
    'gantt2_highlight': ["M14"],
    'architectures': [
        # Table 7 : M1 Métier et formation (3 col)
        ("Unité de formation N° 01 Intitulé : Métier et Formation (30 h)", [
            "Séquence Pédagogique n°1 (Information sur le Métier - 10h)\n-Description générale de la profession\n-Identification des secteurs d'activité\n-Analyse des compétences requises",
            "Séquence Pédagogique n°2 (Information sur la Formation - 10h)\n-Objectifs généraux du programme\n-Modalités d'évaluation et de certification\n-Démarche pédagogique et assiduité",
            "Séquence Pédagogique n°3 (Confirmation de l'Orientation - 10h)\n-Bilan personnel et motivation\n-Projet professionnel de l'apprenant\n-Validation du choix d'orientation"
        ]),
        # Table 8 : M4 Environnement pro (5 col)
        ("Unité de formation n° 04 Intitulé : Environnement professionnel (180 h)", [
            "Séquence Pédagogique n°1 (Contexte aérien - 36h)\n-Description de l'environnement de travail\n-Personnels aéronautiques\n-Instances nationales et internationales\n-Lois et règlements applicables",
            "Séquence Pédagogique n°2 (Contexte maritime - 36h)\n-Description du milieu maritime\n-Personnels et hiérarchie de bord\n-Conventions internationales (OMI)\n-Réglementation transport passagers",
            "Séquence Pédagogique n°3 (Informations de voyage - 36h)\n-Types de voyages et zones géographiques\n-Interprétation des conditions météo\nRègles de régulation du trafic aérien/maritime",
            "Séquence Pédagogique n°4 (Caractéristiques aéronefs - 36h)\n-Différenciation des types d'avions\n-Éléments constitutifs et systèmes\n-Circuits de bord et pressurisation\n-Équipements généraux de bord",
            "Séquence Pédagogique n°5 (Caractéristiques navires - 36h)\n-Types de navires de croisière/ferries\n-Locaux et systèmes de bord\n-Équipements de propulsion et sécurité\n-Zones passagers et d'équipage"
        ]),
        # Table 9 : M5 Comportements (5 col)
        ("Unité de formation n° 05 Intitulé : Comportement et attitudes professionnels (60 h)", [
            "Séquence Pédagogique n°1 (Comportements professionnels - 12h)\n-Langage soigné et courtois\n-Respect strict du port de l'uniforme\n-Règles d'hygiène personnelle\n-Image de marque de la compagnie",
            "Séquence Pédagogique n°2 (Gestion des performances - 12h)\n-Mobilisation des ressources personnelles\n-Gestion efficace du stress et émotions\n-Adaptabilité aux contraintes du bord\n-Endurance et dynamisme",
            "Séquence Pédagogique n°3 (Gestion du temps et priorités - 12h)\n-Planification des tâches quotidiennes\n-Estimation du temps d'exécution\n-Établissement des priorités\n-Gestion des imprévus de service",
            "Séquence Pédagogique n°4 (Communication professionnelle - 12h)\n-Communication verbale et non verbale\n-Courtoisie et sens du service\n-Représentation de l'entreprise\n-Attitude positive constante",
            "Séquence Pédagogique n°5 (Gestion des biens - 12h)\n-Protection des ressources matérielles\n-Standards d'utilisation du matériel\n-Éthique professionnelle et probité\n-Respect des biens de la compagnie"
        ]),
        # Table 10 : M11 Pré-départ (5 col)
        ("Unité de formation n° 11 Intitulé : PROCÉDURES DE PRÉ-DÉPART (60 h)", [
            "Séquence Pédagogique n°1 (Briefing pré-départ - 12h)\n-Ponctualité et présentation générale\n-Recueil et interprétation des informations\n-Attribution des postes et consignes\n-Vérification des documents de vol/mer",
            "Séquence Pédagogique n°2 (Localisation équipements sécurité - 12h)\n-Manuel d'exploitation et conformité\n-Localisation précise du matériel d'urgence\n-Vérification des dates de péremption\n-Rapport de conformité matériel",
            "Séquence Pédagogique n°3 (Contrôle sécurité et sûreté - 12h)\n-Vérification des signaux de fonctionnement\n-Application des consignes de sûreté\n-Contrôle des scellés de cabine\n-Préparation des accès de secours",
            "Séquence Pédagogique n°4 (Contrôle prestations commerciales - 12h)\n-Inspection du matériel hôtelier\n-Vérification des prestations catering\n-Contrôle des kits passagers et confort\n-Approvisionnement des produits de vente",
            "Séquence Pédagogique n°5 (Finalisation pré-départ - 12h)\n-Validation finale de cabine\n-Coordination avec le commandant et sol\n-Autorisation d'embarquement passagers\n-Respect des délais de rotation"
        ]),
        # Table 11 : M14 Secourisme (5 col)
        ("Unité de formation n° 14 Intitulé : Secourisme (165 h)", [
            "Séquence Pédagogique n°1 (Analyse de la situation d'urgence - 33h)\n-Protection de la zone et bilan vital\n-Diagnostic de l'état de la victime\n-Priorisation des gestes de secours\n-Alerte rapide et transmission d'infos",
            "Séquence Pédagogique n°2 (Protocoles d'intervention - 33h)\n-Application des protocoles standardisés\n-Coordination avec l'assistance médicale\n-Utilisation de la trousse médicale\n-Surveillance des fonctions vitales",
            "Séquence Pédagogique n°3 (Gestes de premiers secours - 33h)\n-Réanimation cardio-pulmonaire (RCP)\n-Utilisation du défibrillateur (DAE)\n-Traitement des hémorragies et étouffements\n-Position latérale de sécurité (PLS)",
            "Séquence Pédagogique n°4 (Surveillance post-intervention - 33h)\n-Suivi continu de l'état de la victime\n-Réconfort psychologique et gestion du stress\n-Compte-rendu au personnel médical\n-Rapport d'incident réglementaire",
            "Séquence Pédagogique n°5 (Gestion des urgences spécifiques - 33h)\n-Urgences en vol et en mer isolée\n-Accouchements inopinés et brûlures\n-Malaises cardiaques et respiratoires\n-Débriefing et amélioration des pratiques"
        ])
    ],
    'evaluations': [
        # T13: M5 CC1
        ("Mme Aziza Jouaidi", "COMPORTEMENTS ET ATTITUDES (M5)", "Adoption des comportements professionnels", "Former à adopter un comportement professionnel conforme aux attentes.", "Samedi 02 Août 2025", "03 h (09h00 – 12h00)", "CC1", "Individuel, basé sur des mises en situation pratiques.", "Ponctualité, respect de l'uniforme, courtoisie.", "Évaluation de l'application des obligations professionnelles et du savoir-être."),
        # T14: M11 CC1
        ("Mme Aziza Jouaidi", "PROCÉDURES DE PRÉ-DÉPART (M11)", "Briefing et réunion de pré-départ", "Évaluer la participation active et la compréhension des consignes.", "Lundi 19 Janvier 2026", "03 h (09h00 – 12h00)", "CC1", "En équipe et individuel, briefing simulé.", "Clarté d'expression, exactitude des données, respect du timing.", "Capacité à assimiler les consignes pré-vol/mer et préparer sa zone."),
        # T15: M11 CC2
        ("Mme Aziza Jouaidi", "PROCÉDURES DE PRÉ-DÉPART (M11)", "Localisation des équipements de sécurité", "Vérifier la localisation et conformité des équipements de bord.", "Mardi 20 Janvier 2026", "03 h (09h00 – 12h00)", "CC2", "Inspection pratique cabine avec fiche de contrôle.", "Rapidité de localisation, détection des non-conformités.", "Contrôle réglementaire des équipements d'urgence avant le vol."),
        # T16: M11 CC3
        ("Mme Aziza Jouaidi", "PROCÉDURES DE PRÉ-DÉPART (M11)", "Contrôle des prestations commerciales", "Contrôler le matériel de bord et les prestations de confort.", "Mercredi 21 Janvier 2026", "03 h (09h00 – 12h00)", "CC3", "Vérification des galleys et armements hôteliers.", "Rigueur du contrôle, hygiène, détection des manques.", "Aptitude à assurer l'approvisionnement conforme des prestations passagers."),
        # T17: M11 EFCF Th
        ("Mme Aziza Jouaidi", "PROCÉDURES DE PRÉ-DÉPART (M11)", "Synthèse des connaissances pré-départ", "Valider les connaissances théoriques des procédures pré-départ.", "Jeudi 22 Janvier 2026", "03 h (09h00 – 12h00)", "EFCF Théorique", "Épreuve écrite individuelle sous forme de cas pratiques et QCM.", "Conformité aux manuels d'exploitation, rigueur réglementaire.", "Validation sommative théorique du module M11."),
        # T18: M11 EFCF Pr
        ("Mme Aziza Jouaidi", "PROCÉDURES DE PRÉ-DÉPART (M11)", "Préparation complète de cabine avant départ", "Valider la mise en œuvre pratique de l'ensemble des procédures.", "Vendredi 23 Janvier 2026", "03 h (09h00 – 12h00)", "EFCF Pratique", "Mise en situation réelle sur maquette cabine chronométrée.", "Autonomie, respect des checklists, conformité totale.", "Validation sommative pratique éliminatoire du module M11."),
        # T19: M14 CC1
        ("Mme Aziza Jouaidi", "SECOURISME (M14)", "Bilan vital et réanimation cardio-pulmonaire", "Maîtriser les gestes de réanimation de base.", "Vendredi 05 Février 2027", "03 h (13h00 – 16h00)", "CC1", "Pratique individuelle sur mannequin avec DAE.", "Efficacité des compressions, ventilation, pose DAE.", "Capacité à intervenir immédiatement face à un arrêt cardio-respiratoire."),
        # T20: M14 CC2
        ("Mme Aziza Jouaidi", "SECOURISME (M14)", "Hémorragies et détresses respiratoires", "Traiter les hémorragies graves et obstructions des voies aériennes.", "Vendredi 19 Février 2027", "03 h (13h00 – 16h00)", "CC2", "Cas simulés avec mise en place de pansements compressifs et garrots.", "Rapidité d'arrêt du saignement, manœuvre d'Heimlich correcte.", "Maîtrise des gestes d'urgence vitale hémorragique et respiratoire."),
        # T21: M14 CC3
        ("Mme Aziza Jouaidi", "SECOURISME (M14)", "Traumatologie et malaises", "Prendre en charge traumatismes, brûlures et malaises de bord.", "Vendredi 05 Mars 2027", "03 h (13h00 – 16h00)", "CC3", "Mise en situation de malaise passager en vol/mer.", "Qualité de l'interrogatoire, position d'attente adaptée, réconfort.", "Prise en charge globale d'un passager souffrant à bord."),
        # T22: M14 EFCF Th
        ("Mme Aziza Jouaidi", "SECOURISME (M14)", "Théorie du secourisme et réglementation médicale", "Valider les connaissances théoriques d'intervention d'urgence.", "Vendredi 12 Mars 2027", "03 h (13h00 – 16h00)", "EFCF Théorique", "Épreuve écrite individuelle portant sur la physiologie et protocoles.", "Exactitude des diagnostics, conformité médicale.", "Validation sommative théorique du module M14."),
        # T23: M14 EFCF Pr
        ("Mme Aziza Jouaidi", "SECOURISME (M14)", "Épreuve globale pratique de secourisme de bord", "Valider l'aptitude opérationnelle de sauveteur secouriste.", "Mardi 16 Mars 2027", "03 h (13h00 – 16h00)", "EFCF Pratique", "Intervention complète sur scénario d'accident complexe non annoncé.", "Sang-froid, justesse des gestes, respect des priorités vitales.", "Validation sommative pratique finale du certificat de secourisme.")
    ]
}

# 2. Config Ilham Eddriouich
config_ilham = {
    'key': 'ILHAM',
    'name_upper': 'Mme ILHAM EDDRIOUICH',
    'name_title': 'Mme Ilham Eddriouich',
    'specialite': 'Accueil, Service en vol & Opérations Maritimes',
    'out_docx': r"D:\Piopi\Cahier text\Planning année 2026-2028\Classeur formateur\Classeur-Pédagogique-Formateur-Ilham.docx",
    'modules': [
        ("07", "Approche client", "60", "M7"),
        ("12", "Embarquement et départ", "60", "M12"),
        ("16", "Service durant la croisière", "120", "M16"),
        ("20", "Arrivée et débarquement", "90", "M20"),
        ("18", "Procédures d’urgences aériennes (Volet Pratique)", "60", "M18")
    ],
    'weekly_slots': [
        ("Lundi", "ATAM - 2ème Année\nM16 : Service durant la croisière (Oct-Déc)", "ATAM - 1ère Année : M7 (Sept) / M12 (Jan-Fév)\nATAM - 2ème Année : M20 (Oct-Nov) / M18 (Déc-Jan)", "—"),
        ("Mardi", "ATAM - 2ème Année\nM16 : Service durant la croisière (Oct-Déc)", "ATAM - 1ère Année : M7 (Sept) / M12 (Jan-Fév)\nATAM - 2ème Année : M20 (Oct-Nov) / M18 (Déc-Jan)", "—"),
        ("Mercredi", "ATAM - 2ème Année\nM16 : Service durant la croisière (Oct-Déc)", "ATAM - 1ère Année : M7 (Sept) / M12 (Jan-Fév)\nATAM - 2ème Année : M20 (Oct-Nov) / M18 (Déc-Jan)", "—"),
        ("Jeudi", "ATAM - 2ème Année\nM16 : Service durant la croisière (Oct-Déc)", "ATAM - 1ère Année : M7 (Sept) / M12 (Jan-Fév)\nATAM - 2ème Année : M20 (Oct-Nov) / M18 (Déc-Jan)", "—"),
        ("Vendredi", "ATAM - 2ème Année\nM16 : Service durant la croisière (Oct-Déc)", "ATAM - 1ère Année : M7 (Sept) / M12 (Jan-Fév)\nATAM - 2ème Année : M20 (Oct-Nov) / M18 (Déc-Jan)", "—"),
        ("Samedi", "—", "—", "ATAM - 1ère & 2ème Année : Contrôles Continus (C.C) & Épreuves de Fin de Module (EFCF)\nM7 / M12 / M16 / M20 / M18 (Pratique)")
    ],
    'gantt1_highlight': ["M7", "M12"],
    'gantt2_highlight': ["M16", "M20", "M18"],
    'architectures': [
        # Table 7 : M7 Approche client (3 col)
        ("Unité de formation n° 07 Intitulé : Approche client (60 h)", [
            "Séquence Pédagogique n°1 (Principes relation client & communication - 20h)\n-Communication verbale et non verbale\n-Écoute active et reformulation\n-Attitude professionnelle et empathie\n-Prise en compte des attentes client",
            "Séquence Pédagogique n°2 (Accueil personnalisé & traitement demandes - 20h)\n-Salutations personnalisées\n-Prise en charge immédiate du voyageur\n-Identification des profils passagers\n-Renseignements sur vols et croisières",
            "Séquence Pédagogique n°3 (Gestion des litiges & fidélisation - 20h)\n-Prise en charge des réclamations\n-Désamorçage des conflits et gestion du stress\n-Respect des procédures de compensation\n-Démarche d'amélioration continue"
        ]),
        # Table 8 : M12 Embarquement (5 col)
        ("Unité de formation n° 12 Intitulé : Embarquement et départ (60 h)", [
            "Séquence Pédagogique n°1 (Préparation en porte - 12h)\n-Vérification de la zone d'embarquement\n-Mise en place de la signalétique\n-Coordination avec l'équipe sol\n-Inspection des accès passerelle",
            "Séquence Pédagogique n°2 (Contrôle documentaire - 12h)\n-Vérification des cartes d'accès à bord\n-Contrôle des pièces d'identité et visas\n-Gestion des excédents bagages cabine\n-Respect des règles de sûreté",
            "Séquence Pédagogique n°3 (Gestion des flux passagers - 12h)\n-Embarquement par zones et priorités\n-Prise en charge des passagers PMR et UM\n-Régulation du flux en passerelle\n-Annonces d'embarquement conformes",
            "Séquence Pédagogique n°4 (Accueil et installation à bord - 12h)\n-Accueil chaleureux à l'entrée cabine\n-Guidage vers les rangées et sièges\n-Assistance au rangement des bagages\n-Vérification du dégagement des issues",
            "Séquence Pédagogique n°5 (Clôture et départ - 12h)\n-Comptage passagers et rapprochement\n-Fermeture réglementaire des portes\n-Désarmement passerelle / échelle\n-Transmission du manifeste final"
        ]),
        # Table 9 : M16 Service croisière (5 col)
        ("Unité de formation n° 16 Intitulé : Service durant la croisière (120 h)", [
            "Séquence Pédagogique n°1 (Organisation du service hôtelier - 24h)\n-Planification des rotations de service\n-Vérification matériel hôtelier et galleys\n-Standards de la compagnie\n-Coordination pont et cabine",
            "Séquence Pédagogique n°2 (Restauration et boissons - 24h)\n-Service des repas selon protocole\n-Régimes spéciaux et menus\n-Techniques de service chariot/plateau\n-Règles d'hygiène HACCP",
            "Séquence Pédagogique n°3 (Vente et prestations de bord - 24h)\n-Présentation des boutiques duty free\n-Techniques de conseil produit\n-Encaissement multidevises\n-Gestion des stocks et inventaires",
            "Séquence Pédagogique n°4 (Animation et confort passagers - 24h)\n-Information programme de croisière\n-Activités de loisirs à bord\n-Assistance permanente et veille confort\n-Gestion des cabines et literie",
            "Séquence Pédagogique n°5 (Clôture et bilan traversée - 24h)\n-Rapports de fin de croisière\n-Bilan consommations et ventes\n-Traitement des retours clients\n-Préparation des opérations d'escale"
        ]),
        # Table 10 : M20 Arrivée et débarquement (5 col)
        ("Unité de formation n° 20 Intitulé : Arrivée et débarquement (90 h)", [
            "Séquence Pédagogique n°1 (Préparation de l'arrivée - 18h)\n-Conformité cabine avant atterrissage/accostage\n-Annonces d'arrivée et consignes\n-Coordination avec agents d'escale\n-Positionnement du personnel aux issues",
            "Séquence Pédagogique n°2 (Opérations de débarquement - 18h)\n-Ouverture des portes et passerelle\n-Gestion ordonnée du flux de sortie\n-Respect des priorités de descente\n-Veille sécurité des déplacements",
            "Séquence Pédagogique n°3 (Assistance cas particuliers - 18h)\n-Accompagnement prioritaire PMR/UM\n-Prise en charge personnel sol\n-Vérification des correspondances\n-Assistance médicale si besoin",
            "Séquence Pédagogique n°4 (Inspection post-débarquement - 18h)\n-Fouille de sécurité de la cabine\n-Collecte et inventaire objets oubliés\n-Vérification de l'état général cabine\n-Signalement des anomalies",
            "Séquence Pédagogique n°5 (Rapports et formalités fin voyage - 18h)\n-Compte-rendu de débarquement\n-Transmission documents aux autorités\n-Passation de consignes équipe suivante\n-Clôture administrative de la mission"
        ]),
        # Table 11 : M18 Procédures urgence aériennes Pratique (5 col)
        ("Unité de formation n° 18 Intitulé : Procédures d’urgences aériennes - Volet Pratique (60 h)", [
            "Séquence Pédagogique n°1 (Consignes d'urgence cabine - 12h)\n-Démonstrations sécurité passagers\n-Vérification ceintures et position de sécurité\n-Gestion des issues de secours\n-Commandements vocaux d'urgence",
            "Séquence Pédagogique n°2 (Matériel de sauvetage - 12h)\n-Extincteurs et cagoules anti-fumée\n-Déploiement oxygène fixe et portable\n-Percussion toboggans d'évacuation\n-Lampes torches et gilets de sauvetage",
            "Séquence Pédagogique n°3 (Exercices pratiques d'évacuation - 12h)\n-Évacuation cabine enfumée simulée\n-Ordres d'évacuation terre et ditching\n-Gestion des passagers paniqués\n-Descente toboggan et rassemblement",
            "Séquence Pédagogique n°4 (Situations de crise en vol - 12h)\n-Dépressurisation rapide et masques\n-Lutte contre le feu et fumée cabine\n-Turbulences sévères et sécurisation\n-Communication équipage de conduite/PNC",
            "Séquence Pédagogique n°5 (Survie après évacuation - 12h)\n-Mise en œuvre des canots et radeaux\n-Techniques de survie en mer / milieu hostile\n-Utilisation des balises ELT\n-Organisation du campement de survie"
        ])
    ],
    'evaluations': [
        # T13: M7 CC1
        ("Mme Ilham Eddriouich", "APPROCHE CLIENT (M7)", "Principes de relation client & accueil", "Évaluer la maîtrise des techniques d'accueil et d'écoute active.", "Lundi 15 Septembre 2025", "03 h (13h00 – 16h00)", "CC1", "Mise en situation pratique individuelle et jeux de rôles.", "Courtoisie, clarté d'expression, professionnalisme.", "Aptitude à accueillir un client selon les normes d'excellence."),
        # T14: M7 EFCF
        ("Mme Ilham Eddriouich", "APPROCHE CLIENT (M7)", "Gestion des litiges et réclamations", "Valider la compétence globale en relation client.", "Vendredi 26 Septembre 2025", "03 h (09h00 – 12h00)", "EFCF Théorique & Pratique", "Épreuve sommative et simulation d'un cas complexe.", "Gestion du stress, pertinence des solutions, fidélisation.", "Validation finale du module M7."),
        # T15: M12 CC1
        ("Mme Ilham Eddriouich", "EMBARQUEMENT ET DÉPART (M12)", "Contrôle documentaire en porte", "Évaluer la rigueur dans le filtrage et contrôle passagers.", "Vendredi 30 Janvier 2026", "03 h (13h00 – 16h00)", "CC1", "Simulation d'une file d'embarquement.", "Rapidité, exactitude du contrôle, sûreté.", "Vérification des compétences de filtrage en porte."),
        # T16: M12 CC2
        ("Mme Ilham Eddriouich", "EMBARQUEMENT ET DÉPART (M12)", "Prise en charge des passagers à particularités", "Contrôler l'assistance aux passagers PMR et UM.", "Vendredi 06 Février 2026", "03 h (13h00 – 16h00)", "CC2", "Accompagnement simulé de passagers spécifiques.", "Bienveillance, respect des protocoles, sécurité.", "Prise en charge conforme des publics prioritaires."),
        # T17: M12 EFCF
        ("Mme Ilham Eddriouich", "EMBARQUEMENT ET DÉPART (M12)", "Clôture et départ du vol/navire", "Valider le processus complet d'embarquement.", "Vendredi 13 Février 2026", "03 h (09h00 – 12h00)", "EFCF Théorique & Pratique", "Épreuve pratique intégrée de la porte à la fermeture des accès.", "Gestion du temps de rotation, conformité des annonces.", "Validation finale sommative du module M12."),
        # T18: M20 CC1
        ("Mme Ilham Eddriouich", "ARRIVÉE ET DÉBARQUEMENT (M20)", "Opérations de débarquement sécurisé", "Contrôler la régulation des flux de sortie passagers.", "Vendredi 06 Novembre 2026", "03 h (13h00 – 16h00)", "CC1", "Mise en situation de fin de trajet et sortie passagers.", "Ordre de sortie, consignes de sécurité, courtoisie.", "Évaluation de la gestion des flux de sortie."),
        # T19: M20 EFCF
        ("Mme Ilham Eddriouich", "ARRIVÉE ET DÉBARQUEMENT (M20)", "Inspection cabine et rapports de fin de vol/mer", "Valider les procédures post-débarquement.", "Vendredi 27 Novembre 2026", "03 h (13h00 – 16h00)", "EFCF Théorique & Pratique", "Inspection complète d'appareil et rédaction du compte-rendu.", "Rigueur de la fouille, gestion des objets trouvés.", "Validation finale sommative du module M20."),
        # T20: M16 CC1
        ("Mme Ilham Eddriouich", "SERVICE DURANT LA CROISIÈRE (M16)", "Service hôtelier et restauration de bord", "Évaluer les techniques de service chariot et plateau.", "Vendredi 13 Novembre 2026", "03 h (09h00 – 12h00)", "CC1", "Service d'un repas en cabine reconstituée.", "Protocole hôtelier, hygiène, prestance.", "Maîtrise des standards de service de bord."),
        # T21: M16 CC2
        ("Mme Ilham Eddriouich", "SERVICE DURANT LA CROISIÈRE (M16)", "Vente duty-free et gestion commerciale", "Contrôler la maîtrise de la vente de bord.", "Vendredi 04 Décembre 2026", "03 h (09h00 – 12h00)", "CC2", "Vente conseil en boutique et tenue de caisse.", "Argumentaire, rapidité de calcul, service client.", "Aptitude à valoriser les ventes annexes."),
        # T22: M16 EFCF
        ("Mme Ilham Eddriouich", "SERVICE DURANT LA CROISIÈRE (M16)", "Gestion globale de la croisière", "Valider l'ensemble des compétences de service à bord.", "Vendredi 18 Décembre 2026", "03 h (09h00 – 12h00)", "EFCF Théorique & Pratique", "Épreuve de synthèse sur un cycle de navigation.", "Professionnalisme, réactivité face aux imprévus.", "Validation finale sommative du module M16."),
        # T23: M18 EFCF Pr
        ("Mme Ilham Eddriouich", "PROCÉDURES D’URGENCE AÉRIENNES (M18)", "Évacuation d'urgence et sauvetage pratique", "Valider les gestes réflexes d'évacuation cabine.", "Samedi 16 Janvier 2027", "03 h (13h00 – 16h00)", "EFCF Pratique", "Évacuation chronométrée sur maquette avec toboggan.", "Autorité des ordres vocaux, rapidité, sécurité.", "Validation pratique éliminatoire du module M18.")
    ]
}

# 3. Config Rachid El Sabah
config_rachid = {
    'key': 'RACHID',
    'name_upper': 'M. RACHID EL SABAH',
    'name_title': 'M. Rachid El Sabah',
    'specialite': 'Sûreté, Marchandises Dangereuses, Réglementation & Informatique',
    'out_docx': r"D:\Piopi\Cahier text\Planning année 2026-2028\Classeur formateur\Classeur-Pédagogique-Formateur-Rachid El Sabah.docx",
    'modules': [
        ("09", "Mesures de sûreté", "45", "M9"),
        ("10", "Marchandises dangereuses", "45", "M10"),
        ("02", "Outils informatiques", "30", "M2"),
        ("18", "Procédures d’urgences aériennes (Volet Théorique & Réglementaire)", "30", "M18"),
        ("19", "Procédures d’urgences maritimes", "90", "M19")
    ],
    'weekly_slots': [
        ("Lundi", "ATAM - 1ère Année : M9 (Déc 25) / M10 (Déc-Jan) / M2 (Fév-Mar)\nATAM - 2ème Année : M19 (Déc 26 - Fév 27)", "ATAM - 1ère Année : M9 / M10 / M2\nATAM - 2ème Année : M18 Théorie (Nov-Déc 26)", "—"),
        ("Mardi", "ATAM - 1ère Année : M9 (Déc 25) / M10 (Déc-Jan) / M2 (Fév-Mar)\nATAM - 2ème Année : M19 (Déc 26 - Fév 27)", "ATAM - 1ère Année : M9 / M10 / M2\nATAM - 2ème Année : M18 Théorie (Nov-Déc 26)", "—"),
        ("Mercredi", "ATAM - 1ère Année : M9 (Déc 25) / M10 (Déc-Jan) / M2 (Fév-Mar)\nATAM - 2ème Année : M19 (Déc 26 - Fév 27)", "ATAM - 1ère Année : M9 / M10 / M2\nATAM - 2ème Année : M18 Théorie (Nov-Déc 26)", "—"),
        ("Jeudi", "ATAM - 1ère Année : M9 (Déc 25) / M10 (Déc-Jan) / M2 (Fév-Mar)\nATAM - 2ème Année : M19 (Déc 26 - Fév 27)", "ATAM - 1ère Année : M9 / M10 / M2\nATAM - 2ème Année : M18 Théorie (Nov-Déc 26)", "—"),
        ("Vendredi", "ATAM - 1ère Année : M9 (Déc 25) / M10 (Déc-Jan) / M2 (Fév-Mar)\nATAM - 2ème Année : M19 (Déc 26 - Fév 27)", "ATAM - 1ère Année : M9 / M10 / M2\nATAM - 2ème Année : M18 Théorie (Nov-Déc 26)", "—"),
        ("Samedi", "—", "—", "ATAM - 1ère & 2ème Année : Contrôles Continus (C.C) & Épreuves de Fin de Module (EFCF)\nM9 / M10 / M2 / M18 / M19")
    ],
    'gantt1_highlight': ["M9", "M10", "M2"],
    'gantt2_highlight': ["M18", "M19"],
    'architectures': [
        # Table 7 : M9 Sûreté (3 col)
        ("Unité de formation n° 09 Intitulé : Mesures de sûreté (45 h)", [
            "Séquence Pédagogique n°1 (Contexte réglementaire et cadre juridique - 15h)\n-Réglementation internationale OACI (Annexe 17)\n-Réglementation nationale de sûreté aéroportuaire/portuaire\n-Typologie des actes d'intervention illicite\n-Rôles des services de sécurité et de police",
            "Séquence Pédagogique n°2 (Mesures préventives et contrôle d'accès - 15h)\n-Inspection-filtrage des passagers et bagages de cabine\n-Contrôle des bagages de soute et du fret aérien/maritime\n-Gestion des titres d'accès en zone réservée\n-Fouille de sécurité et protection des aéronefs/navires",
            "Séquence Pédagogique n°3 (Gestion des menaces et procédures d'urgence - 15h)\n-Procédures d'alerte en cas de découverte d'objet suspect\n-Gestion des passagers indisciplinés ou menaçants\n-Mesures en cas de prise d'otage ou détournement\n-Rapports d'incident et débriefing de sûreté"
        ]),
        # Table 8 : M10 Marchandises dangereuses (5 col)
        ("Unité de formation n° 10 Intitulé : Marchandises dangereuses (45 h)", [
            "Séquence Pédagogique n°1 (Réglementation IATA / OACI & Classification - 9h)\n-Cadre légal du transport des matières dangereuses\n-Présentation des 9 classes de danger\n-Notion de quantités limitées et exceptées\n-Responsabilités des intervenants de la chaîne",
            "Séquence Pédagogique n°2 (Étiquetage, marquage et documentation - 9h)\n-Reconnaissance des étiquettes de danger et de manutention\n-Lecture de la déclaration d'expédition (DGD)\n-Fiche d'instruction pour l'équipage (NOTOC)\n-Vérification de la conformité documentaire",
            "Séquence Pédagogique n°3 (Bagages passagers et exemptions - 9h)\n-Articles autorisés ou interdits transportés par passagers\n-Réglementation des batteries lithium et appareils électroniques\n-Médicaments et produits de toilette exemptés\n-Procédures d'information et filtrage passagers",
            "Séquence Pédagogique n°4 (Stockage, chargement et séparation - 9h)\n-Règles d'incompatibilité et de séparation des colis\n-Procédures de chargement en soute sécurisée\n-Arrimage et protection contre les avaries\n-Contrôle avant départ de l'intégrité des colis",
            "Séquence Pédagogique n°5 (Procédures d'urgence en cas d'incident - 9h)\n-Mesures immédiates face à une fuite ou émanation toxique\n-Utilisation de la trousse d'intervention d'urgence\n-Isolement de la zone contaminée et aération\n-Transmission de l'alerte et consignes d'intervention"
        ]),
        # Table 9 : M2 Outils informatiques (5 col)
        ("Unité de formation n° 02 Intitulé : Outils informatiques (30 h)", [
            "Séquence Pédagogique n°1 (Environnement informatique professionnel - 6h)\n-Système d'exploitation et arborescence de fichiers\n-Sécurité des données et mots de passe professionnels\n-Périphériques d'entrée/sortie et impression\n-Hygiène numérique et sauvegardes",
            "Séquence Pédagogique n°2 (Traitement de texte professionnel - 6h)\n-Rédaction de notes de service et mémos\n-Mise en page de rapports d'activité\n-Création de tableaux et formulaires types\n-Publipostage et modèles de documents",
            "Séquence Pédagogique n°3 (Tableur appliqué aux transports - 6h)\n-Création de tableaux de bord et plannings de vol\n-Formules de calcul, moyennes et pourcentages\n-Suivi statistique de fréquentation et ponctualité\n-Graphiques d'analyse d'activité commerciale",
            "Séquence Pédagogique n°4 (Communication et messagerie pro - 6h)\n-Gestion professionnelle de la messagerie électronique\n-Organisation des dossiers et règles de messagerie\n-Partage d'agendas et planification de réunions\n-Outils collaboratifs en ligne",
            "Séquence Pédagogique n°5 (Initiation aux progiciels métiers - 6h)\n-Introduction aux systèmes GDS et DCS de base\n-Consultation des horaires et disponibilités\n-Recherche de dossiers passagers (PNR)\n-Principes de saisie des données passagers"
        ]),
        # Table 10 : M18 Urgences aériennes Théorie (5 col)
        ("Unité de formation n° 18 Intitulé : Procédures d’urgences aériennes - Volet Théorique & Réglementaire (30 h)", [
            "Séquence Pédagogique n°1 (Cadre réglementaire de sécurité aérienne - 6h)\n-Réglementation internationale OACI et EASA\n-Manuel d'exploitation compagnie (Part A & B)\n-Rôles et responsabilités du commandant et de l'équipage\n-Culture de sécurité et retours d'expérience (SGS)",
            "Séquence Pédagogique n°2 (Typologie des urgences techniques en vol - 6h)\n-Dépressurisation cabine lente et explosive\n-Panne moteur, perte des servitudes et atterrissage forcé\n-Phénomènes météorologiques extrêmes et turbulences\n-Procédures d'urgence associées à chaque panne",
            "Séquence Pédagogique n°3 (Incendie et fumée à bord - 6h)\n-Causes potentielles d'incendie (fours, galleys, soutes, toilettes)\n-Classification des feux et agents extincteurs autorisés\n-Procédures de lutte contre le feu en espace confiné\n-Protection respiratoire de l'équipage et des passagers",
            "Séquence Pédagogique n°4 (Facteurs humains et communication de crise - 6h)\n-Gestion du stress et de la charge de travail (CRM)\n-Communication claire et standardisée sol-bord et inter-équipage\n-Prise de décision collective sous contrainte temporelle\n-Gestion des réactions émotionnelles des passagers",
            "Séquence Pédagogique n°5 (Préparation à l'évacuation d'urgence - 6h)\n-Critères de décision d'évacuation terre et amerrissage\n-Briefing d'urgence de l'équipage et des passagers (NITS)\n-Attribution des tâches aux passagers valides (ABPs)\n-Coordination avec les services de secours au sol"
        ]),
        # Table 11 : M19 Urgences maritimes (5 col)
        ("Unité de formation n° 19 Intitulé : Procédures d’urgences maritimes (90 h)", [
            "Séquence Pédagogique n°1 (Réglementation maritime & conventions - 18h)\n-Convention SOLAS et Code ISM\n-Organisation de la sécurité à bord d'un navire\n-Plan de gestion des urgences et rôle d'appel\n-Obligations de formation et d'entraînement (STCW)",
            "Séquence Pédagogique n°2 (Signaux sonores et procédures d'alerte - 18h)\n-Signaux d'alarme générale et d'abandon du navire\n-Rassemblement ordonné des passagers aux postes de rassemblement\n-Distribution et ajustement des gilets de sauvetage\n-Vérification des listes d'appel et comptage",
            "Séquence Pédagogique n°3 (Lutte contre les avaries et incendies - 18h)\n-Compartimentage étanche et fermeture des portes étanches\n-Organisation des équipes d'intervention incendie de bord\n-Utilisation des moyens fixes et mobiles d'extinction\n-Procédures en cas d'envahissement par l'eau et gîte",
            "Séquence Pédagogique n°4 (Abandon du navire et embarcations - 18h)\n-Ordre officiel d'abandon et préparation des embarcations\n-Mise à l'eau des canots et radeaux pneumatiques\n-Embarquement méthodique des passagers par ordre de priorité\n-Manœuvre des bossoirs et largage des amarres",
            "Séquence Pédagogique n°5 (Survie en mer et secours maritimes - 18h)\n-Règles d'hygiène et de rationnement à bord des canots\n-Utilisation des engins pyrotechniques (fusées, fumigènes)\n-Mise en œuvre des balises de détresse EPIRB et transpondeurs SART\n-Coordination avec les centres de sauvetage en mer (MRCC)"
        ])
    ],
    'evaluations': [
        # T13: M9 CC1
        ("M. Rachid El Sabah", "MESURES DE SÛRETÉ (M9)", "Cadre réglementaire et actes d'intervention illicite", "Évaluer la maîtrise des règles internationales de sûreté.", "Vendredi 12 Décembre 2025", "03 h (09h00 – 12h00)", "CC1", "Épreuve individuelle écrite avec études de cas.", "Rigueur réglementaire, identification des menaces.", "Connaissance des mesures de sûreté applicables."),
        # T14: M9 EFCF
        ("M. Rachid El Sabah", "MESURES DE SÛRETÉ (M9)", "Inspection-filtrage et procédures de crise", "Valider les réflexes face aux situations de menace.", "Jeudi 25 Décembre 2025", "03 h (09h00 – 12h00)", "EFCF Théorique & Pratique", "Mise en situation pratique de contrôle et détection.", "Rapidité d'alerte, respect des protocoles de sûreté.", "Validation finale sommative du module M9."),
        # T15: M10 CC1
        ("M. Rachid El Sabah", "MARCHANDISES DANGEREUSES (M10)", "Classification des 9 classes et étiquetage", "Contrôler l'identification des marchandises dangereuses.", "Mardi 30 Décembre 2025", "03 h (09h00 – 12h00)", "CC1", "Exercice d'identification d'étiquettes et colis.", "Exactitude de classification, détection des risques.", "Maîtrise des 9 classes de danger IATA/OACI."),
        # T16: M10 EFCF
        ("M. Rachid El Sabah", "MARCHANDISES DANGEREUSES (M10)", "Stockage, exemptions et procédures d'urgence", "Valider la conformité du traitement des matières dangereuses.", "Vendredi 09 Janvier 2026", "03 h (09h00 – 12h00)", "EFCF Théorique & Pratique", "Simulation d'incident fuite/colis suspect et analyse DGD.", "Mesures de protection immédiate, conformité NOTOC.", "Validation finale sommative du module M10."),
        # T17: M2 CC1
        ("M. Rachid El Sabah", "OUTILS INFORMATIQUES (M2)", "Bureautique appliquée : traitement de texte et tableur", "Évaluer la production de documents professionnels de transport.", "Vendredi 20 Février 2026", "03 h (13h00 – 16h00)", "CC1", "Épreuve pratique sur poste informatique.", "Mise en page, exactitude des formules tableur.", "Capacité à produire des documents de suivi d'activité."),
        # T18: M2 EFCF
        ("M. Rachid El Sabah", "OUTILS INFORMATIQUES (M2)", "Progiciels métiers et synthèse informatique", "Valider la maîtrise des outils informatiques professionnels.", "Mercredi 04 Mars 2026", "03 h (09h00 – 12h00)", "EFCF Pratique", "Épreuve sommative pratique sur progiciel de transport.", "Rapidité de saisie, consultation des bases passagers.", "Validation finale sommative du module M2."),
        # T19: M18 CC Th
        ("M. Rachid El Sabah", "PROCÉDURES D’URGENCE AÉRIENNES (M18)", "Réglementation et pannes en vol", "Évaluer les connaissances théoriques des procédures d'urgence.", "Vendredi 11 Décembre 2026", "03 h (13h00 – 16h00)", "CC1", "Contrôle théorique sur cas d'urgence en vol.", "Respect des checklists, compréhension des pannes.", "Assimilation des protocoles de secours en vol."),
        # T20: M18 EFCF Th
        ("M. Rachid El Sabah", "PROCÉDURES D’URGENCE AÉRIENNES (M18)", "Synthèse théorique sécurité et sauvetage", "Valider la maîtrise théorique du module M18.", "Vendredi 18 Décembre 2026", "03 h (13h00 – 16h00)", "EFCF Théorique", "Épreuve sommative théorique approfondie.", "Maîtrise réglementaire OACI, gestion CRM.", "Validation finale théorique sommative du module M18."),
        # T21: M19 CC1
        ("M. Rachid El Sabah", "PROCÉDURES D’URGENCE MARITIMES (M19)", "Convention SOLAS et signaux d'alerte à bord", "Contrôler la connaissance des signaux et du rôle d'appel.", "Vendredi 08 Janvier 2027", "03 h (09h00 – 12h00)", "CC1", "Questionnaire et exercice de rassemblement passagers.", "Exactitude des signaux sonores, ordre d'évacuation.", "Connaissance des procédures initiales d'alerte en mer."),
        # T22: M19 CC2
        ("M. Rachid El Sabah", "PROCÉDURES D’URGENCE MARITIMES (M19)", "Lutte contre les avaries et abandon du navire", "Évaluer la mise en œuvre des moyens de sauvetage.", "Vendredi 22 Janvier 2027", "03 h (09h00 – 12h00)", "CC2", "Étude de cas sur scénario de voie d'eau et abandon.", "Procédures de mise à l'eau des radeaux, priorités.", "Maîtrise des protocoles d'évacuation maritime."),
        # T23: M19 EFCF
        ("M. Rachid El Sabah", "PROCÉDURES D’URGENCE MARITIMES (M19)", "Survie en mer et synthèse urgences maritimes", "Valider la qualification sécurité maritime globale.", "Vendredi 05 Février 2027", "03 h (09h00 – 12h00)", "EFCF Théorique & Pratique", "Épreuve sommative complète écrite et simulation pratique.", "Utilisation pyrotechnie, balises EPIRB, survie en mer.", "Validation finale sommative du module M19.")
    ]
}

if __name__ == "__main__":
    print("Building Aziza Jouaidi...")
    build_teacher_classeur(config_aziza)
    print("Building Ilham Eddriouich...")
    build_teacher_classeur(config_ilham)
    print("Building Rachid El Sabah...")
    build_teacher_classeur(config_rachid)
    print("All 3 teacher classeurs generated successfully!")
