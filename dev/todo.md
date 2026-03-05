# TODO

## ✅ Fait
- [x] Validation pour chaque modèle (`Job`, `Article`, `Filiere`, `Category`, `Sector`, `Table`)
- [x] Filtrage des entités invalides du JSON final (`filter_invalid()`)
- [x] Enrichissement / imputation des données manquantes (`enrich()`)
- [x] Nullification des références pendantes après filtrage

---

## 🔧 En cours
- [ ] Ramener les filières et catégories dans le JSON final (vérifier le parsing)
- [ ] Corriger le parsing des catégories manquantes sur les jobs

---

## 📋 À faire

### Pipeline
- [ ] Sauvegarder les entités invalides dans un `errors.json` séparé
- [ ] Ajouter un rapport de parsing (nb jobs extraits, nb filtrés, nb enrichis)

### Qualité des données
- [ ] Améliorer la détection des lignes d'en-tête dans `TableParser`
- [ ] Améliorer le split male/female des titres de postes sans séparateur `/`
- [ ] Valider les salaires contre les minima légaux connus

### Outillage
- [ ] Interface GUI pour corriger les données et sauvegarder les corrections
- [ ] Modèle IA entraîné sur les corrections manuelles

---

## 💡 Idées futures
- [ ] Support d'autres conventions collectives (IDCC différents)
- [ ] Export vers base de données (PostgreSQL, MongoDB)
- [ ] API REST pour exposer les données parsées