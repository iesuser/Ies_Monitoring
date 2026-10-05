# Seismic Events — Design & UI (Implemented)

ეს დოკუმენტი აღწერს **იმპლემენტირებულ** Seismic Events მოდულს: API ქცევას, Web UI-ს და კლიენტის ნაკადებს.  
API endpoint-ების მოკლე ცხრილი: [`09-api-inventory.md`](09-api-inventory.md).

---

## 1. უფლებები

| Code | UI / API |
|------|----------|
| `can_event_view` | სიის, ფილტრის, დეტალების და beachball/magnitude ნახვა |
| `can_event_edit` | შექმნა, რედაქტირება, წაშლა; magnitude და beachball CRUD |
| `can_event_publish` | WordPress publish / unpublish (API + დეტალების გვერდის publish panel); ასევე იძლევა seismic read უფლებას |

`can_event_edit` ასევე იძლევა read უფლებას. Publish ცალკე უფლებაა (`can_event_publish`).

Navbar → Events ჩანს თუ მომხმარებელს აქვს რომელიმე ამ უფლებიდან.

---

## 2. Web UI გვერდები

| Path | აღწერა |
|------|--------|
| `/<lang>/seismic_events` | სია, რუკა (Leaflet), ფილტრები, შექმნა/რედაქტირება მოდალებით |
| `/<lang>/seismic_events/<id>` | Event details — summary banner, publish panel, tab-ები |

i18n: EN/KA (`app/static/js/i18n.js`).

### 2.1 სია (`events.html`)

- **რუკა + ფილტრები** ზედა ზონაში; ქვემოთ earthquake ცხრილი.
- **ცხრილის სვეტები:** Action · Earthquake Time · Magnitude · Location (`location_en` EN-ზე, `location_ge` KA-ზე).
- **Actions:** Details · Edit · Delete (`can_event_edit`-ისთვის Edit/Delete).
- Details ღილაკი გადაჰყავს `/seismic_events/<id>`-ზე.
- **Add Earthquake** — მხოლოდ `can_event_edit`.

### 2.2 ფილტრაცია (server-side)

კლიენტი **არ ფილტრავს** სრულ სიას ბრაუზერში. Apply / Reset იძახებს API-ს:

| მდგომარეობა | Request |
|-------------|---------|
| ცარიელი ფილტრი / Reset | `GET /api/seismic_events/` |
| აქტიური ფილტრი | `POST /api/seismic_events/filter` |

ფილტრის ველები და API mapping:

| UI ველი | API body |
|---------|----------|
| Event ID | `event_query` (substring on id **ან** `iesdata_id`) |
| SeisComP OID | `seiscomp_oid` |
| Location | `location` (`location_en` / `location_ge`) |
| Area | `area` |
| Magnitude rows | ერთი სტრიქონი → `magnitude` / `magnitude_min` / `magnitude_max`; რამდენიმე → `magnitudes: [{…}]` (AND) |
| Depth min/max | `depth_min` / `depth_max` |
| Date from/to | `date_from` / `date_to` (ISO 8601) |

თარიღის UI: Flatpickr, ფორმატი **`dd/mm/yyyy`**.

შექმნა/რედაქტირება/წაშლის შემდეგ სია ხელახლა იტვირთება აქტიური ფილტრით.

### 2.3 შექმნა / რედაქტირება (მოდალები)

ველების თანმიმდევრობა:

1. IES data ID · SeisComP OID  
2. Origin Time (ISO 8601) * · Depth (km) *  
3. Latitude * · Longitude *  
4. Location GE · Location EN · Area  
5. Magnitudes  
6. Beachball (Strike · Dip · Rake)

**Origin time (UI):** ტექსტური ველი; paste/შენახვა **timezone shift-ის გარეშე**.

მიღებული ფორმატები:

- `YYYY-MM-DD HH:mm:ss` → ინახება `YYYY-MM-DDTHH:mm:ss`
- `YYYY-MM-DDTHH:mm:ss`
- `dd/mm/yyyy, HH:mm:ss` (ასევე მხარდაჭერილი)

ცხრილში და დეტალებზე დრო ჩანს როგორც **`YYYY-MM-DDTHH:mm:ss`**.

**Beachball UI ვალიდაცია:** `strike`, `dip`, `rake` ან სამივე შევსებული, ან სამივე ცარიელი. ნაწილობრივი შევსებისას მოდალში **warning** და submit არ გრძელდება.

შექმნისას შევსებული beachball იგზავნება `POST .../beachball`-ით event-ის შექმნის შემდეგ.  
რედაქტირებისას — `POST` (თუ არ იყო) ან `PUT` (თუ იყო); წაშლა ცალკე ღილაკით.

### 2.4 Event details (`eventDetails.html`)

სტრუქტურა:

1. Back + სათაური + Edit/Delete (`can_event_edit`)
2. **Summary banner** — Origin time, Magnitude, Depth, Lat/Lon, Event ID + OID / IES meta
3. **Publish panel** (summary-ის ქვემოთ) — გამოქვეყნების სტატუსი და მოქმედებები
4. **Tab-ები:**
   - Overview — სრული მეტამონაცემები
   - Magnitudes — ცხრილი
   - Beachball — PNG + strike/dip/rake
   - Map — Leaflet, ერთი მოვლენის მარკერი

Edit იხსნება **იმავე გვერდის მოდალში** (სიაზე არ გადადის). შენახვის შემდეგ დეტალები იქვე ახლდება.  
Delete → სიაზე დაბრუნება.

#### Publish panel (`can_event_publish`)

- სტატუსი: **Published** / **Not published** (+ `published_at` თუ გამოქვეყნებულია).
- თუ გამოუქვეყნებელია: **Publish**.
- თუ უკვე გამოქვეყნებულია: **Update publish** + **Unpublish**.
- API:
  - `POST /api/publish_events/publish/<id>`
  - `POST /api/publish_events/unpublish/<id>`
- Publish-მდე event-ს სჭირდება მინიმუმ ერთი magnitude (API 400 თუ არ აქვს).
- წარმატების შემდეგ UI იღებს განახლებულ `event`-ს (`is_published`, `published_at`) და პანელს ხელახლა ხატავს.

---

## 3. API ქცევა (დეტალები)

### 3.1 Create / Update event

| ველი | Create API | UI |
|------|------------|-----|
| `origin_time` | required | required |
| `latitude`, `longitude` | required | required |
| `depth` | optional | required (UI) |
| `iesdata_id`, `seiscomp_oid`, locations, `area` | optional | optional |
| `is_automatic` | optional (default false) | არ იცვლება UI-დან შექმნისას |

Event JSON ასევე შეიცავს `is_published` და `published_at` (`published_events` ურთიერთობიდან).

### 3.2 Filter

ყველა ველი optional; პირობები **AND**.  
`date_from` / `date_to` — ISO 8601 datetime.  
მრავალი მაგნიტუდის კრიტერიუმი — `magnitudes` სია, თითო EXISTS subquery (AND).

### 3.3 Beachball

- ერთ event-ზე მაქსიმუმ ერთი ჩანაწერი.
- `strike` / `dip` / `rake`: **სამივე ან არცერთი** (API 400 თუ ნაწილობრივი).
- სამივეს არსებობისას სერვერი აგენერირებს PNG-ს (`ObsPy beachball`) →  
  `/static/beachballs/beachball_<event_id>.png` და ინახავს `beachball_path`-ში.
- კლიენტის მიერ გამოგზავნილი `beachball_path` **იგნორდება**.

გენერაცია: `app/utils/gen_beachball_img.py`.

### 3.4 Publish / Unpublish (WordPress)

დეტალები: [`09-api-inventory.md`](09-api-inventory.md) — Publish Events.  
კლიენტი: `app/utils/wp_publish_client.py`. კონფიგი: `WP_PUBLISH_CODE` (და WP URL env/config-ში).

---

## 4. Frontend ფაილები

| ფაილი | როლი |
|-------|------|
| `app/views/seismic_events/routes.py` | `/seismic_events`, `/seismic_events/<id>` |
| `app/templates/seismic_events/events.html` | სია + რუკა |
| `app/templates/seismic_events/eventDetails.html` | დეტალები (summary, publish panel, tabs) |
| `app/templates/seismic_events/filterEvent.html` | ფილტრის ფორმა |
| `app/templates/seismic_events/createEvent.html` | შექმნის მოდალი |
| `app/templates/seismic_events/editEvent.html` | რედაქტირების მოდალი |
| `app/static/js/seismic_events/events.js` | სია, auth, filter apply orchestration |
| `app/static/js/seismic_events/filterEvent.js` | ფილტრის state → API payload |
| `app/static/js/seismic_events/createEvent.js` | შექმნა + magnitudes + beachball |
| `app/static/js/seismic_events/editEvent.js` | რედაქტირება + magnitudes + beachball |
| `app/static/js/seismic_events/eventDetailsPage.js` | დეტალების გვერდი + publish panel |
| `app/static/js/seismic_events/eventDetail.js` | Actions: details button + Event ID link |
| `app/static/js/seismic_events/map.js` | სიის Leaflet რუკა |
| `app/static/js/seismic_events/deleteEvent.js` | წაშლა სიიდან |
| `app/static/css/styles.css` | summary / publish panel სტილები |

API: `app/api/seismic_events.py`, `app/api/nsmodels/seismic_events.py`,  
`app/api/publish_events.py`, `app/api/nsmodels/publish_events.py`  
Models: `seismic_events`, `magnitudes`, `event_magnitudes`, `event_beachball`, `published_events`

---

## 5. ტესტები

`tests/test_seismic_events_api.py` — CRUD, filter, beachball all-or-none, PNG path და სხვ.  
`tests/test_publish_events_api.py` — publish / unpublish / public list.

```bash
pytest tests/test_seismic_events_api.py tests/test_publish_events_api.py -q
```
