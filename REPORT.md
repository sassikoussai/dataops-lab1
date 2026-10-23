# REPORT.md — TP guidé 1 : D'un script fragile à un pipeline testé

**Binôme :** _(vos deux noms ici)_  
**Date :** 2026-10-23

---

## Q1 — Pourquoi requirements.txt ?

On écrit les bibliothèques dans equirements.txt au lieu de taper simplement
pip install pandas parce que le fichier sert de **mémoire reproductible** du projet.
N'importe qui (coéquipier, serveur CI, machine future) peut recréer exactement le même
environnement en une seule commande pip install -r requirements.txt, sans avoir à
se souvenir quelles bibliothèques installer ni dans quelle version.
Sans ce fichier, les installations sont éphémères : elles ne sont pas versionnées,
pas partagées, et le projet cesse de fonctionner dès qu'on change de machine.

---

## Q2 — Combien de lignes dans le rapport naïf ?

Le rapport affiche **7 lignes** au lieu de 5.  
Les raisons : 	unisia (minuscule) et MOROCCO (majuscules) sont traités comme des
pays différents de Tunisia et Morocco. Le regroupement groupby est sensible à
la casse, donc la même réalité géographique apparaît sous plusieurs orthographes.

---

## Q3 — Cinq problèmes trouvés dans orders_day1.csv

| order_id | Problème observé | Dimension de qualité |
|----------|-----------------|----------------------|
| 1004 | quantity = -2 (quantité négative) | **Validité** |
| 1008 | customer_id vide | **Complétude** |
| 1013 | order_date = 2026-13-45 (date impossible) | **Validité** |
| 1019 | unit_price = 4500.0 (prix aberrant pour un clavier) | **Exactitude** |
| 1006 | country = tunisia (casse incorrecte) | **Cohérence** |
| 1016 | country = MOROCCO (casse incorrecte) | **Cohérence** |
| 1010 | order_id 1010 apparaît deux fois (doublon) | **Unicité** |
| 1023 | country = " Tunisia" (espace en tête) | **Cohérence** |

_(Au moins cinq problèmes différents identifiés — plusieurs dimensions sont représentées.)_

---

## Q4 — Le total est-il trop haut ou trop bas ?

On ne peut **pas le savoir avec certitude** sans recalculer à la main, car les erreurs
jouent dans les deux sens :

- Les erreurs qui **gonflent** le total : unit_price = 4500 pour un clavier (règle 4),
  le doublon sur 1010 qui double une commande (règle 5).
- Les erreurs qui **réduisent** le total : la quantité négative −2 × 19.9 = −39.8
  est soustraite du total (règle 3).

En pratique, le total naïf (12 771,10) est **trop élevé** par rapport au vrai total
(7 655,90), mais on ne peut pas le deviner sans outiller les contrôles.

---

## Q5 — Avantages du découpage en fonctions

1. **Testabilité** : chaque fonction peut être testée indépendamment avec des données
   synthétiques. On peut vérifier clean_orders sans lire un vrai fichier.
2. **Lisibilité et maintenabilité** : chaque étape a une responsabilité claire et un nom
   explicite (extract, alidate, 	ransform, load). Quand un bug apparaît, on sait
   immédiatement dans quelle fonction chercher.

---

## Q6 — Bon total et erreur de l'ancien script

- **Bon total :** 7 655,90 €
- **Total naïf :** 12 771,10 €
- **Écart :** +5 115,20 €
- **En pourcentage :** (12771.10 − 7655.90) / 7655.90 ≈ +66,8 %

L'ancien script **surestimait le chiffre d'affaires de presque 67 %**.

---

## Q7 — Commande principale responsable de l'erreur

La commande **1019** (order_id 1019) : unit_price = 4500.0 pour un clavier
au lieu de 45,0. Cela ajoute 4 455 € fictifs au total (4 500 − 45 = 4 455).  
C'est la **règle 4** (invalid_unit_price, prix > MAX_UNIT_PRICE = 1000) qui l'a capturée.

---

## Q8 — Pourquoi enregistrer les lignes rejetées ?

On enregistre les lignes rejetées dans data/rejected/rejected_orders.csv plutôt que
de simplement les supprimer pour trois raisons :

1. **Traçabilité** : on peut auditer pourquoi une commande a été exclue du rapport.
2. **Correction en amont** : l'équipe source peut identifier et corriger l'erreur dans
   le système d'origine (ex. : le prix à 4 500 € est une faute de saisie à corriger).
3. **Non-perte de données** : une ligne rejetée aujourd'hui peut être valide demain
   après correction ; la supprimer serait irréversible.

---

## Q9 — Que s'est-il passé quand on a cassé la règle 3 ?

En remplaçant > 0 par > -5, les quantités négatives (ex. : −2) ne sont plus marquées
comme invalides. Le test **	est_negative_quantity_is_rejected** a échoué :
il attendait que la commande avec quantity = -2 soit dans ejected, mais elle
se retrouvait dans clean. pytest affichait 1 failed, 4 passed.

---

## Q10 — Test unitaire vs contrôle de données

- **Test unitaire** : vérifie que la **logique du code** est correcte, en exécutant une
  fonction sur un petit tableau fabriqué à la main dont on connaît déjà la bonne réponse.
- **Contrôle de données** : vérifie que les **données réelles du jour** respectent les
  règles métier, à chaque exécution du pipeline sur les vraies données.

---

## Q11 — Tableau comparatif ancien script vs pipeline

|  | Ancien script | Votre pipeline |
|--|--------------|----------------|
| **Jour 2 : message d'erreur ?** | Non — aucune erreur | Oui — PIPELINE STOPPED: Reject rate too high: 100% (6/6 rows rejected, limit is 20%) |
| **Jour 2 : total affiché** | 543 500,00 (faux) | Aucun (pipeline arrêté) |
| **Jour 3 : message d'erreur ?** | Non — aucune erreur (KeyError sur unit_price) | Oui — PIPELINE STOPPED: Missing columns: ['unit_price'] |

---

## Q12 — Ce qui a changé dans le système source

- **Jour 2** : Les prix ont été **multipliés par 100** (ex. : 449 → 44 900). C'est
  probablement un changement d'unité dans le système source (centimes au lieu d'euros)
  ou une erreur d'export. Toutes les lignes dépassent MAX_UNIT_PRICE = 1000.
- **Jour 3** : La colonne unit_price a été **renommée price** dans le fichier
  source. C'est une rupture de contrat de schéma (breaking schema change).

---

## Q13 — Jour le plus dangereux sans pipeline

Le **jour 2** est le plus dangereux. Voici pourquoi :

- Au jour 3, l'ancien script plante avec une KeyError sur unit_price : l'erreur
  est visible, personne ne reçoit de chiffre.
- Au jour 2, l'ancien script **ne plante pas** et affiche un total de 543 500 € au lieu
  de quelques milliers. Le directeur commercial reçoit un chiffre **faux mais
  plausible-looking**, sans aucun avertissement. C'est une erreur silencieuse :
  la plus dangereuse car on la croit vraie.

---

## Q14 — À quoi sert le code de sortie 1 ?

Le code de sortie 1 peut être utilisé par :

1. **Un orchestrateur** (ex. : Apache Airflow, cron, GitHub Actions) pour détecter
   l'échec et déclencher une alerte ou stopper les tâches suivantes qui dépendraient
   de ce rapport.
2. **Un système de monitoring** pour envoyer une notification (email, Slack, PagerDuty)
   à l'équipe data.
3. **Un script shell** qui teste if [ True -ne 0 ]; then ... pour brancher un
   comportement d'erreur.
4. **Une pipeline CI/CD** (GitHub Actions) pour marquer le job comme échoué et bloquer
   un déploiement.
