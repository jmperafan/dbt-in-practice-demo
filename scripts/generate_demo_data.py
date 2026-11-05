#!/usr/bin/env python3
"""Generate the raw, synthetic data for Sutton Tennis Club.

Writes CSVs to data/raw/. Deterministic (seeded) so re-running produces the
same files. Stdlib only, on purpose, so cloning this repo and running this
script needs nothing beyond a plain Python 3 install.

Every table here is fictional. The data model's shape (members, coaches,
court reservations, lessons, tournaments, invoices) mirrors a real club's
operations, but no row in any file describes a real person or event.

A few quirks are injected on purpose, each one feeding a specific lesson's
live demo rather than being organic mess:

  - court_reservations: start_time/end_time are sometimes a bare "HH:MM"
    string and sometimes a full timestamp string, the same mixed-format
    problem a real export would hand you. Motivates staging's cast/normalize
    job (Lesson 3).
  - member_id / coach_id foreign keys: ~5% resolve to a "GHOST-####" id that
    matches no real member or coach, simulating a deleted record or a data
    entry error. Motivates relationships tests (Lesson 6) and the sources
    contract discussion (Lesson 3).
  - court_reservations: a handful of rows are exact duplicates of another
    row, simulating a reload that re-sent the same batch. Motivates the
    idempotent-load / merge-vs-append discussion (Lesson 3).
  - court_reservations: a handful of rows have a loaded_at far later than
    their reservation_date, simulating a late-arriving backfill. Motivates
    --defer and dbt State's lag_tolerance (Lesson 4/8).

Run it again with a different --seed to get a different (still internally
consistent) dataset.
"""

import argparse
import csv
import datetime
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "data", "raw")

FIRST_NAMES = [
    "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "Logan", "Mia", "Lucas", "Amelia", "Jack", "Harper", "Aiden",
    "Evelyn", "Owen", "Abigail", "Henry", "Emily", "Leo", "Elizabeth", "Max",
    "Charlotte", "Sam", "Grace", "Daniel", "Chloe", "Oliver", "Victoria",
    "James", "Hannah", "Ben", "Zoe", "Alex", "Lily", "Will", "Nora", "Theo",
]
LAST_NAMES = [
    "Carter", "Bennett", "Hughes", "Foster", "Simmons", "Patel", "Ramirez",
    "Cooper", "Morgan", "Russell", "Bailey", "Reed", "Kelly", "Price",
    "Sanders", "Wood", "Barnes", "Ross", "Henderson", "Coleman", "Jenkins",
    "Perry", "Powell", "Long", "Patterson", "Hughes", "Flores", "Washington",
    "Butler", "Simmons", "Foster", "Gonzales", "Bryant", "Alexander", "Russell",
]
CITIES = ["Hartwell", "Rosedale", "Brookside", "Elmwood", "Ashford", "Millbrook"]


def person_name(rng):
    return rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)


def email_for(first, last, i):
    return f"{first.lower()}.{last.lower()}{i}@example.com"


def phone_for(rng):
    return f"555-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}"


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows):>5} rows -> {os.path.relpath(path)}")


def maybe_ghost(rng, real_id, rate=0.05):
    """Returns real_id most of the time, an orphaned GHOST id rate% of the time."""
    if rng.random() < rate:
        return f"GHOST-{rng.randint(1000, 9999)}"
    return real_id


def generate(seed, n_members, n_reservations, n_lessons):
    rng = random.Random(seed)
    today = datetime.date(2026, 11, 1)
    start_date = today - datetime.timedelta(days=365)

    # ---- members ---------------------------------------------------------
    members = []
    member_ids = []
    for i in range(1, n_members + 1):
        first, last = person_name(rng)
        member_id = f"M-{i:04d}"
        member_ids.append(member_id)
        joined = start_date - datetime.timedelta(days=rng.randint(0, 365 * 4))
        members.append({
            "member_id": member_id,
            "first_name": first,
            "last_name": last,
            "email": email_for(first, last, i),
            "phone": phone_for(rng),
            "date_of_birth": (today - datetime.timedelta(days=rng.randint(365 * 8, 365 * 75))).isoformat(),
            "join_date": joined.isoformat(),
            "membership_tier": rng.choices(
                ["Junior", "Adult", "Family", "Senior"], weights=[15, 50, 20, 15]
            )[0],
            "city": rng.choice(CITIES),
            "is_active": rng.random() > 0.08,
            "loaded_at": datetime.datetime.combine(
                joined, datetime.time(hour=rng.randint(6, 20))
            ).isoformat(sep=" "),
        })

    # ---- coaches -----------------------------------------------------------
    coach_specs = [
        ("Junior development", "Certified"), ("Competitive", "Master"),
        ("Adult beginner", "Certified"), ("Cardio tennis", "Professional"),
        ("Competitive", "Elite"), ("Junior development", "Professional"),
        ("Adult beginner", "Certified"), ("Doubles strategy", "Master"),
    ]
    coaches = []
    coach_ids = []
    for i, (specialty, cert) in enumerate(coach_specs, start=1):
        first, last = person_name(rng)
        coach_id = f"COACH-{i:02d}"
        coach_ids.append(coach_id)
        hire_date = start_date - datetime.timedelta(days=rng.randint(30, 365 * 6))
        coaches.append({
            "coach_id": coach_id,
            "first_name": first,
            "last_name": last,
            "email": email_for(first, last, i),
            "phone": phone_for(rng),
            "hire_date": hire_date.isoformat(),
            "specialty": specialty,
            "certification_level": cert,
            "hourly_rate": rng.choice([45.00, 55.00, 65.00, 80.00, 95.00]),
            "is_active": rng.random() > 0.1,
            "loaded_at": datetime.datetime.combine(
                hire_date, datetime.time(hour=9)
            ).isoformat(sep=" "),
        })

    # ---- court_reservations (the big, messy raw fact) ----------------------
    booking_types = ["Court Booking", "Lesson", "Tournament", "Maintenance", "Closed"]
    reservations = []
    for i in range(1, n_reservations + 1):
        res_id = f"RES-{i:05d}"
        res_date = start_date + datetime.timedelta(days=rng.randint(0, 365))
        hour = rng.randint(7, 21)
        minute = rng.choice([0, 30])
        duration_hours = rng.choice([0.5, 1.0, 1.0, 1.0, 1.5, 2.0])
        start_dt = datetime.datetime.combine(res_date, datetime.time(hour, minute))
        end_dt = start_dt + datetime.timedelta(hours=duration_hours)

        # Quirk: ~15% of rows render start/end as a full timestamp string
        # instead of a bare "HH:MM" string — the mixed-format problem.
        if rng.random() < 0.15:
            start_time = start_dt.isoformat(sep=" ")
            end_time = end_dt.isoformat(sep=" ")
        else:
            start_time = start_dt.strftime("%H:%M")
            end_time = end_dt.strftime("%H:%M")

        booking_type = rng.choices(booking_types, weights=[70, 15, 5, 5, 5])[0]
        member_id = maybe_ghost(rng, rng.choice(member_ids)) if booking_type != "Maintenance" else ""

        created_at = datetime.datetime.combine(
            res_date - datetime.timedelta(days=rng.randint(0, 10)),
            datetime.time(hour=rng.randint(8, 20), minute=rng.randint(0, 59)),
        )
        loaded_at = created_at + datetime.timedelta(minutes=rng.randint(1, 30))
        # Quirk: ~3% of rows arrive very late — a backfill days after the event.
        if rng.random() < 0.03:
            loaded_at = loaded_at + datetime.timedelta(days=rng.randint(8, 21))

        reservations.append({
            "reservation_id": res_id,
            "court_number": rng.randint(1, 6),
            "member_id": member_id,
            "reservation_date": res_date.isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "duration_hours": duration_hours,
            "booking_type": booking_type,
            "status": rng.choices(
                ["Confirmed", "Cancelled", "Unconfirmed"], weights=[85, 10, 5]
            )[0],
            "booking_source": rng.choice(["Admin", "App", "Phone"]),
            "created_at": created_at.isoformat(sep=" "),
            "loaded_at": loaded_at.isoformat(sep=" "),
        })

    # Quirk: duplicate ~2% of rows verbatim — a reload that re-sent a batch.
    n_dupes = max(1, int(n_reservations * 0.02))
    reservations += [dict(r) for r in rng.sample(reservations, n_dupes)]
    rng.shuffle(reservations)

    # ---- lessons -------------------------------------------------------------
    lessons = []
    for i in range(1, n_lessons + 1):
        lesson_date = start_date + datetime.timedelta(days=rng.randint(0, 365))
        created_at = datetime.datetime.combine(
            lesson_date - datetime.timedelta(days=rng.randint(1, 14)),
            datetime.time(hour=rng.randint(8, 18)),
        )
        lessons.append({
            "lesson_id": f"LESSON-{i:04d}",
            "member_id": maybe_ghost(rng, rng.choice(member_ids)),
            "coach_id": rng.choice(coach_ids),
            "court_number": rng.randint(1, 6),
            "lesson_date": lesson_date.isoformat(),
            "start_time": f"{rng.randint(7, 20):02d}:{rng.choice([0, 30]):02d}",
            "duration_minutes": rng.choice([30, 45, 60, 90]),
            "lesson_type": rng.choices(
                ["Private", "Semi-private", "Group", "Clinic"], weights=[40, 20, 30, 10]
            )[0],
            "skill_level": rng.choice(["Beginner", "Intermediate", "Advanced"]),
            "price": rng.choice([35.00, 45.00, 60.00, 75.00, 90.00]),
            "status": rng.choices(
                ["Booked", "Completed", "Cancelled", "No-show"], weights=[10, 75, 10, 5]
            )[0],
            "created_at": created_at.isoformat(sep=" "),
            "loaded_at": (created_at + datetime.timedelta(minutes=rng.randint(1, 20))).isoformat(sep=" "),
        })

    # ---- tournaments, entries, matches -----------------------------------
    tournament_defs = [
        ("Spring Singles Open", "Singles", 3), ("Summer Doubles Classic", "Doubles", 4),
        ("Junior Invitational", "Junior", 2), ("Mixed Doubles Cup", "Mixed", 3),
        ("Veterans Championship", "Veterans", 2), ("Fall Singles Open", "Singles", 3),
        ("Club Doubles League", "Doubles", 4), ("Winter Junior Series", "Junior", 2),
    ]
    tournaments, entries, matches = [], [], []
    entry_i, match_i = 1, 1
    for t_i, (name, category, rounds) in enumerate(tournament_defs, start=1):
        t_id = f"T-{t_i:03d}"
        t_start = start_date + datetime.timedelta(days=rng.randint(0, 330))
        t_end = t_start + datetime.timedelta(days=rng.choice([1, 2, 3]))
        tournaments.append({
            "tournament_id": t_id,
            "name": name,
            "start_date": t_start.isoformat(),
            "end_date": t_end.isoformat(),
            "category": category,
            "entry_fee": rng.choice([15.00, 20.00, 25.00, 30.00]),
            "max_participants": rng.choice([16, 32]),
            "season_year": t_start.year,
            "loaded_at": datetime.datetime.combine(t_start, datetime.time(9)).isoformat(sep=" "),
        })

        participants = rng.sample(member_ids, k=min(16, len(member_ids)))
        placements = ["Champion", "Runner-up"] + ["Semifinalist"] * 2 + ["Eliminated"] * (len(participants) - 4)
        for seed, (member_id, placement) in enumerate(zip(participants, placements), start=1):
            entries.append({
                "entry_id": f"ENTRY-{entry_i:04d}",
                "tournament_id": t_id,
                "member_id": maybe_ghost(rng, member_id),
                "registration_date": (t_start - datetime.timedelta(days=rng.randint(3, 21))).isoformat(),
                "seed": seed,
                "entry_fee_paid": tournaments[-1]["entry_fee"],
                "final_placement": placement,
                "loaded_at": datetime.datetime.combine(t_start, datetime.time(9)).isoformat(sep=" "),
            })
            entry_i += 1

        for r in range(rounds):
            p1, p2 = rng.sample(participants, 2)
            winner = rng.choice([p1, p2])
            match_date = t_start + datetime.timedelta(days=r)
            matches.append({
                "match_id": f"MATCH-{match_i:04d}",
                "tournament_id": t_id,
                "player1_member_id": p1,
                "player2_member_id": p2,
                "court_number": rng.randint(1, 6),
                "match_date": match_date.isoformat(),
                "start_time": f"{rng.randint(9, 17):02d}:00",
                "duration_minutes": rng.choice([60, 75, 90, 120]),
                "winner_member_id": winner,
                "score": rng.choice(["6-4, 6-3", "7-5, 6-7, 6-2", "6-2, 6-2", "6-4, 4-6, 6-3"]),
                "round_name": f"Round {r + 1}",
                "loaded_at": datetime.datetime.combine(match_date, datetime.time(20)).isoformat(sep=" "),
            })
            match_i += 1

    # ---- invoices + line items -------------------------------------------
    invoices, line_items = [], []
    line_i = 1
    invoice_categories = [
        ("Membership", 1, (40.00, 120.00)),
        ("Court Fee", 2, (10.00, 25.00)),
        ("Lesson", 1, (35.00, 90.00)),
        ("Tournament Entry", 1, (15.00, 30.00)),
    ]
    for i in range(1, int(n_members * 2.0) + 1):
        inv_id = f"INV-{i:05d}"
        inv_date = start_date + datetime.timedelta(days=rng.randint(0, 365))
        due_date = inv_date + datetime.timedelta(days=30)
        member_id = maybe_ghost(rng, rng.choice(member_ids))
        status = rng.choices(["Paid", "Pending", "Overdue"], weights=[75, 15, 10])[0]
        paid_date = (
            (inv_date + datetime.timedelta(days=rng.randint(1, 25))).isoformat()
            if status == "Paid" else ""
        )

        n_lines = rng.choice([1, 1, 2, 2, 3])
        chosen = rng.sample(invoice_categories, k=min(n_lines, len(invoice_categories)))
        total = 0.0
        for category, qty, (lo, hi) in chosen:
            unit_amount = round(rng.uniform(lo, hi), 2)
            line_amount = round(unit_amount * qty, 2)
            total += line_amount
            line_items.append({
                "line_item_id": f"LI-{line_i:05d}",
                "invoice_id": inv_id,
                "category": category,
                "description": f"{category} charge",
                "quantity": qty,
                "unit_amount": unit_amount,
                "line_amount": line_amount,
                "loaded_at": datetime.datetime.combine(inv_date, datetime.time(6)).isoformat(sep=" "),
            })
            line_i += 1

        invoices.append({
            "invoice_id": inv_id,
            "member_id": member_id,
            "invoice_date": inv_date.isoformat(),
            "due_date": due_date.isoformat(),
            "total_amount": round(total, 2),
            "status": status,
            "payment_method": rng.choice(["Credit Card", "Bank Transfer", "Cash"]),
            "paid_date": paid_date,
            "loaded_at": datetime.datetime.combine(inv_date, datetime.time(6)).isoformat(sep=" "),
        })

    return {
        "members": (members, list(members[0].keys())),
        "coaches": (coaches, list(coaches[0].keys())),
        "court_reservations": (reservations, list(reservations[0].keys())),
        "lessons": (lessons, list(lessons[0].keys())),
        "tournaments": (tournaments, list(tournaments[0].keys())),
        "tournament_entries": (entries, list(entries[0].keys())),
        "matches": (matches, list(matches[0].keys())),
        "invoices": (invoices, list(invoices[0].keys())),
        "invoice_line_items": (line_items, list(line_items[0].keys())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--members", type=int, default=220)
    parser.add_argument("--reservations", type=int, default=4000)
    parser.add_argument("--lessons", type=int, default=350)
    args = parser.parse_args()

    tables = generate(args.seed, args.members, args.reservations, args.lessons)
    for name, (rows, fieldnames) in tables.items():
        write_csv(os.path.join(OUT_DIR, f"{name}.csv"), fieldnames, rows)


if __name__ == "__main__":
    main()
