# ------------------------------------------------------------
# GET ACCUMULATOR STATUS + ODDS (READ‑ONLY)
# ------------------------------------------------------------
@router.get("/", response_model=schemas.AccumulatorOut)
def get_accumulator(db: Session = Depends(get_db)):
    print(">>> ACCA ROUTE HIT <<<")

    picks = (
        db.query(models.Pick)
        .options(joinedload(models.Pick.player))
        .filter(models.Pick.status.in_(["Pending", "Win", "Place", "Lose", "NR"]))
        .all()
    )

    for p in picks:
        print("PICK:", p.id, p.status, p.odds_fraction, p.player_id)

    if not picks:
        return schemas.AccumulatorOut(
            picks=[],
            combined_decimal_odds=None,
            ew_250_potential_return=None,
            win_acca_odds=None,
            place_acca_odds=None,
            status="no picks",
        )

    active = [p for p in picks if p.status != "NR"]

    if not active:
        return schemas.AccumulatorOut(
            picks=picks,
            combined_decimal_odds=None,
            ew_250_potential_return=None,
            win_acca_odds=None,
            place_acca_odds=None,
            status="all non runners",
        )

    # (rest of your logic continues normally…)


    # --------------------------------------------------------
    # REAL EACH-WAY ACCA LOGIC
    # --------------------------------------------------------
    win_acca = 1.0
    place_acca = 1.0

    for p in active:
        dec = fractional_to_decimal(p.odds_fraction)
        place_dec = place_decimal(dec)

        if p.status == "Win":
            win_acca *= dec
            place_acca *= place_dec

        elif p.status == "Place":
            win_acca = 0
            place_acca *= place_dec

        elif p.status == "Lose":
            win_acca = 0
            place_acca = 0
            break

        elif p.status == "Pending":
            win_acca *= dec
            place_acca *= place_dec

    # --------------------------------------------------------
    # DETERMINE ACCA STATUS
    # --------------------------------------------------------
    if win_acca == 0 and place_acca == 0:
        status = "lose"
    elif all(p.status == "Win" for p in active):
        status = "win"
    elif any(p.status == "Place" for p in active):
        status = "place"
    else:
        status = "live"

    # --------------------------------------------------------
    # £2.50 E/W stake = £2.50 win + £2.50 place
    # --------------------------------------------------------
    win_return = 2.5 * win_acca
    place_return = 2.5 * place_acca
    ew_total = win_return + place_return

    return schemas.AccumulatorOut(
        picks=picks,
        combined_decimal_odds=win_acca,
        ew_250_potential_return=ew_total,
        win_acca_odds=win_acca,
        place_acca_odds=place_acca,
        status=status,
    )
