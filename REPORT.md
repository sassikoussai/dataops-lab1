## TP3 — Du pipeline Python à l'ELT moderne avec DuckDB et dbt

**Résultat final (jour 1)** :

```
Done. PASS=14 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=14
```

Total du rapport `revenue_by_country` : **8835.4**, identique à `run_pipeline.py`.
Commit : `c80c59a Move the transformation to SQL with dbt and DuckDB`.

---

### Étape 1 — Extract + Load

**Q1. Pourquoi charger toutes les colonnes en texte ?**
Si DuckDB devine les types, il choisit `INTEGER` pour `quantity` d'après les premières lignes. Le jour où une quantité vaut « deux », le chargement lui-même plante et on n'a plus de brut dans l'entrepôt. En chargeant tout en `VARCHAR`, aucune ligne n'est refusée au chargement : les valeurs invalides (`-2`, `2026-13-45`, « deux ») arrivent telles quelles et c'est le SQL des couches suivantes qui décide, avec un motif de rejet explicite.

**Q2. Le total naïf en SQL est aussi faux que celui de Python.**
Le langage n'a aucune importance : SQL calcule aussi faussement que pandas si on ne vérifie rien (13950.6 au lieu de 8835.4). Ce qui rend un pipeline fiable, ce sont les règles de qualité, les tests et l'arrêt de la chaîne en cas de problème, pas le choix de l'outil.

**Q3. Avantage d'avoir gardé le brut dans l'entrepôt.**
Si une règle de nettoyage est fausse, on corrige le SQL et on recalcule tout depuis `raw.orders`, sans retourner chercher le fichier source. Le brut est aussi la preuve de ce qui a été reçu (avec `_source_file` et `_loaded_at`), donc on peut auditer et rejouer.

---

### Étape 2 — Projet dbt

**Q4. `profiles.yml` en entreprise (Snowflake, BigQuery).**
Il faut changer `type` (`snowflake`, `bigquery`) et remplacer `path` par les paramètres de connexion (compte, utilisateur, base, schéma, entrepôt, rôle, ou projet et jeu de données). Le mot de passe ne doit jamais être écrit en clair dans le fichier ni commité : on le lit depuis une variable d'environnement (`{{ env_var('DBT_PASSWORD') }}`) alimentée par un gestionnaire de secrets (secrets CI, coffre-fort), comme vu à la séance 2.

---

### Étape 3 — Staging

**Q5. Pourquoi ne pas supprimer la commande 1013 dès le staging ?**
Le staging type et répare, il ne juge pas. Si on supprimait la ligne ici, elle disparaîtrait sans trace, et on ne pourrait plus ni l'expliquer ni la corriger. Le rejet doit être explicite : la ligne reste, reçoit le motif `invalid_date` dans `int_orders_checked`, et finit en quarantaine dans `orders_rejected`.

**Q6. `stg_orders` est une vue.**
Lire une vue relance son `select` sur `raw.orders` à chaque lecture : rien n'est stocké. C'est acceptable en staging car la transformation est légère (des casts et un nettoyage de texte), les données sont toujours fraîches et il n'y a pas de seconde copie à maintenir. Les marts, eux, sont des tables car ils sont lus par les utilisateurs.

---

### Étape 4 — Les six règles et le rapport

**Q7. Remplacement de `{{ ref('stg_orders') }}`.**
Dans `target/compiled/shop/models/intermediate/int_orders_checked.sql`, dbt remplace `ref('stg_orders')` par le nom qualifié de la vue : `"warehouse"."main"."stg_orders"`. Le `ref()` sert donc à deux choses : produire le bon nom de table et fixer l'ordre de construction.

**Q8. `row_number() over (partition by order_id order by _row_number)`.**
La fonction regroupe les lignes par `order_id` et les numérote 1, 2, 3… dans l'ordre de `_row_number`. La ligne de rang 1 est la première apparition, les rangs supérieurs sont les doublons, d'où `> 1` pour la règle 5. C'est l'équivalent de `df.duplicated("order_id", keep="first")`. `_row_number` est nécessaire car SQL ne garantit aucun ordre de lecture : sans lui, « la première » n'aurait pas de sens et le résultat pourrait changer d'une exécution à l'autre.

**Q9. Chiffre d'affaires par produit.**
L'analyste crée `models/marts/revenue_by_product.sql`, un simple `select` avec `group by product` sur `{{ ref('orders_clean') }}`. Il n'a pas à toucher au Python : dbt déduit l'ordre grâce à `ref()` et le modèle apparaît dans le lignage.

---

### Étape 5 — Tests de données et `dbt build`

**Q10. Casser la règle 5.**
Sans la règle 5, les doublons ne sont plus rejetés. *À COMPLÉTER avec ta sortie : noter quel test a échoué en premier (le test unitaire `test_duplicate_order_keeps_the_first` s'exécute avant le modèle, puis `unique_orders_clean_order_id` sur les vraies données) et la liste des `SKIP`.* Les modèles et tests en aval du test en échec (dont `revenue_by_country`) sont `SKIP`. C'est exactement ce que l'on veut : le rapport du directeur commercial n'est pas reconstruit avec de mauvaises données et la version de la veille reste en place.

**Q11. Correspondances TP1 → dbt.**

| Contrôle du TP1 (Python) | Son équivalent dbt |
|---|---|
| `check_schema` | L'échec de `stg_orders` quand une colonne manque (erreur de liaison, vue au jour 3), et les tests génériques (`not_null`, `unique`, `accepted_values`) |
| Les règles 1 à 6 dans `clean_orders` | Le `case when` de `int_orders_checked.sql` (la première règle vraie gagne) |
| `check_reject_rate` | Le test singulier `assert_reject_rate_below_20_percent` |
| `rejected_orders.csv` | Le modèle `orders_rejected` (table de quarantaine) |
| `PIPELINE STOPPED`, rien n'est publié | `dbt build` échoue, les modèles en aval passent en `SKIP`, code de sortie 1 |

---

### Étape 6 — Test unitaire

**Q12. D'où venaient les données du test unitaire ?**
Elles viennent du fichier YAML lui-même (le bloc `given` avec des lignes écrites à la main), pas de `load_raw.py` ni d'un CSV. En CI (séance 4), le test peut donc tourner sans entrepôt chargé ni fichier de données : il est rapide, reproductible et indépendant des données réelles. On teste uniquement la logique SQL.

---

### Étape 7 — Lignage

**Q13. `country` arrive vide dans la source.**
Modèles touchés, en suivant le graphe : `stg_orders`, puis `int_orders_checked` (les lignes seraient rejetées en `unknown_country`), puis `orders_clean`, `orders_rejected` et `revenue_by_country`. Avec le graphe, la réponse prend quelques secondes (`+` / `stg_orders+`). Sans lui, dans un dossier de 200 scripts SQL, il faudrait ouvrir et lire chaque fichier pour retrouver les dépendances : plusieurs dizaines de minutes, avec un risque d'oubli.

---

### Étape 8 — Jours 2 et 3

**Q14. Comparaison des pipelines.**

| | Pipeline Python (TP1) | Pipeline dbt (TP3) |
|---|---|---|
| Jour 2 : quel contrôle arrête la chaîne ? | `check_reject_rate` | Test `assert_reject_rate_below_20_percent` (`FAIL 1`), puis 9 étapes en `SKIP` |
| Jour 3 : quel message d'erreur ? | À COMPLÉTER : message de `check_schema` au TP1 | `Binder Error: Table "src" does not have a column named "unit_price"`, `Candidate bindings: "price"` (13 étapes en `SKIP`) |
| Le rapport de la veille est-il conservé ? | Oui, rien n'est écrit | Oui, `revenue_by_country` vaut toujours 8835.4 |
| Code de sortie | À COMPLÉTER : valeur notée au TP1 (non nul) | 1 (vérifié avec `$LASTEXITCODE`) |

Le jour 2 est arrêté par un test de données (données reçues mais mauvaises), le jour 3 par une erreur de construction (la structure du fichier a changé).

**Q15. La quarantaine du jour 2.**
Oui, c'est un problème : `orders_rejected` est en `SKIP`, donc elle contient encore les rejets du jour 1, alors que ce sont ceux du jour 2 qu'il faudrait examiner pour comprendre l'échec. Proposition : séparer la quarantaine du chemin qui mène au rapport. Deux façons :
1. Construire la quarantaine **avant** le blocage : lancer `dbt run --select +orders_rejected` puis `dbt build` (dans un script ou en CI). La quarantaine du jour est publiée, le rapport reste bloqué.
2. Restructurer les modèles pour que le test de taux de rejet ne bloque que `orders_clean` et ses descendants, et pas `orders_rejected`.

On peut aussi garder l'historique des rejets en ajoutant `_source_file` dans la quarantaine, pour distinguer les jours.

---

### Étape 9 — Commit

```
c80c59a (HEAD -> main) Move the transformation to SQL with dbt and DuckDB
d63a8ec Add DuckDB and dbt to requirements
```

`git status` : `working tree clean`. `warehouse.duckdb`, `target/` et `logs/` ne sont pas versionnés.