# Lee's Wholesale Inventory Tracking System

COMP2140 group WED_10-12_G05. Python 3.10+ with **tkinter** (screens) and **sqlite3** (storage). No installs needed.
The code follows the layers in our SDS: `app/screens` (Screen layer), `app/logic` (Logic layer), `app/data` (Data layer).

## Run it
    python -m app.data.seed --demo      # once: creates the database with demo users and products
    python main.py                      # sign in with manager / manager123
    python -m unittest discover -s tests -t . -v      # run all tests

Demo logins: `manager`, `owner`, `warehouse`, `cashier` (password = name + `123`).
Demo products are dated from today so every boundary case works: Rice (low stock), Sugar (exactly at the
threshold), Milk (10 days), Yogurt (exactly 30 days), Cheese (31 days), Butter (expires today), Juice (expired 2 days ago).

## Who built what (six features, one each)
| Person | Feature | Edit ONLY these files | Status |
|---|---|---|---|
| Jaekwon | FID-1 Add Product, skeleton, database | `product_manager.py` (add_product), `product_screen.py` (add form), `database.py` | done |
| Brandon | FID-3 Update Product | `product_manager.py` (update_product), `product_screen.py` (edit form), `tests/test_fid3_update_product.py` | done |
| Ricardo | FID-5 Low-stock alert | `alert_manager.py` (low_stock_alerts), `alert_screen.py`, `tests/test_fid5_low_stock.py` | done |
| Tevin | FID-6 Nearing-expiry notification | `alert_manager.py` (nearing_expiry_notifications), `tests/test_fid6_nearing_expiry.py` | done |
| D'mitri | FID-10 Record Damage, BusinessRules | `stock_manager.py` (record_damage), `damage_screen.py`, `rules.py`, `tests/test_fid10_record_damage.py` | done |
| Janae | FID-11 Expired status, login polish | `stock_manager.py` (expire_overdue), `expiry_timer.py`, `idle_lock.py` + `main.py` (15-min idle lock), `tests/test_fid11_expired_status.py`, `tests/test_idle_lock.py` | done |

FID-2 (remove), FID-4 (stock changes), FID-7 (search), FID-8 (status), FID-9 (record a sale) and the backup were added on 25 Nov, so there are now tests for them too: `tests/test_fid2_remove_product.py`, `test_fid4_stock_change.py`, `test_fid7_search.py`, `test_fid8_status.py`, `test_fid9_record_sale.py`, `test_backup.py`.
All eleven features are implemented. Every manager method follows the same pattern as `add_product`:
permission check -> validate -> apply rules -> ONE transaction -> audit log row.
Each `tests/test_fid*.py` has one test per SRS test scenario; the two marked "Manual (GUI)" in `test_fid10_record_damage.py` are checked by hand on the screen.
Run everything with `python -m unittest` (shared set-up is in `tests/helpers.py`).

## Rules for everyone
- Screens never contain rules. They call one manager and show the result.
- Only `app/data/database.py` touches the data file. Pass values with `?` placeholders, never by joining strings into SQL.
- Never store or print passwords. Quantities can never go negative. Related changes are saved in ONE `db.transaction()`.
- Rules (30 days, low-stock, expiry) live only in `app/logic/rules.py`.

## Working together on GitHub
1. ONE person creates an empty repository (no README), adds everyone as collaborators, and pushes this folder:

        git init -b main
        git add .
        git commit -m "Starter project"
        git remote add origin https://github.com/<owner>/<repo>.git
        git push -u origin main
2. Everyone else: `git clone <repo-url>`
3. Work on your own branch, and commit often:

        git checkout -b fid5-low-stock
        git add .
        git commit -m "FID-5: low-stock alerts"
        git pull --rebase origin main
        git push -u origin fid5-low-stock
   Then open a Pull Request on GitHub and merge it into `main` (or merge it yourself if you are the only one who touched those files).
4. Before you start work each time: `git checkout main && git pull`.
5. Final: tag the demo version so the marker sees exactly what we demo: `git tag final-submission && git push --tags`.
   The submission PDF must link to this repository. It can't be changed after the demo.

## Known limits
- The tkinter screens were checked with a stand-in for tkinter, not on a real screen. Expect to fix small layout issues on first run.
- Permissions per role are the defaults in `ROLE_PERMISSIONS` (`app/logic/models.py`), the same table as SRS 3.2.2 and SDS 2.3.1. The client must still approve them.
- Built in this version: all eleven features, FID-1 to FID-11 (+ login, 15-minute idle lock, audit log, automatic backups). Backups go to the `backups` folder (newest 7 kept) at start-up and every 24 hours; managers and owners also have a 'Back up now' button. Protecting the data file itself is left to Windows file permissions (SEC-5), not the program.
- The 'Run expiry check now' button is a demo aid. The real check runs at start-up and every 24 hours.
- Screen checks that need a real window (pop-up text, form values kept after an error, the edit dialog) are listed as manual tests in the Test Plan.
- A damage entry larger than the first batch is taken from the batch that expires first, then the next one, and one damage record is saved per batch used.
