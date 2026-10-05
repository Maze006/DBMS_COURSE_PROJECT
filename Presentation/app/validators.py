import re
from datetime import date

from db import ValidationError

KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{7,99}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BILLING_CYCLES = ("Monthly", "Quarterly", "Annual")
LICENSE_STATUSES = ("Active", "Expired", "Revoked")


def _raise(errors):
    if errors:
        raise ValidationError(errors)


def clean(text):
    text = (text or "").strip()
    return text or None


def validate_purchase(license_type_id, quantity, unit_cost, purchase_date, order_reference,
                      license_key, start_date, end_date, billing_cycle, cost_per_cycle):
    e = []
    if not license_type_id:
        e.append("Select a license type.")
    if not isinstance(quantity, int) or quantity <= 0:
        e.append("Quantity must be a whole number greater than zero.")
    elif quantity > 100000:
        e.append("Quantity can't exceed 100,000.")
    if unit_cost is None or unit_cost < 0:
        e.append("Unit cost can't be negative.")
    elif unit_cost > 10_000_000:
        e.append("Unit cost looks too large. Check the amount.")
    if not isinstance(purchase_date, date):
        e.append("Enter a purchase date.")
    if not (isinstance(start_date, date) and isinstance(end_date, date)):
        e.append("Enter the license start and end dates.")
    elif end_date <= start_date:
        e.append("The license end date must be after its start date.")
    elif isinstance(purchase_date, date) and purchase_date > end_date:
        e.append("The purchase date can't be after the license end date.")
    if license_key and not KEY_RE.match(license_key):
        e.append("License key must be 8-100 characters: letters, digits and hyphens only.")
    if order_reference and len(order_reference) > 50:
        e.append("Order reference can't exceed 50 characters.")
    if billing_cycle:
        if billing_cycle not in BILLING_CYCLES:
            e.append("Choose a valid billing cycle.")
        if cost_per_cycle is None or cost_per_cycle <= 0:
            e.append("Cost per billing cycle must be greater than zero.")
    _raise(e)


def validate_license_update(license_key, quantity, start_date, end_date, status):
    e = []
    if not license_key or not KEY_RE.match(license_key):
        e.append("License key must be 8-100 characters: letters, digits and hyphens only.")
    if not isinstance(quantity, int) or quantity <= 0:
        e.append("Quantity must be a whole number greater than zero.")
    if end_date <= start_date:
        e.append("The license end date must be after its start date.")
    if status not in LICENSE_STATUSES:
        e.append("Choose a valid status.")
    _raise(e)


def validate_allocation(license_id, user_id, department_id, allocated_date, expiry_date):
    e = []
    if not license_id:
        e.append("Select a license.")
    if not user_id:
        e.append("Select a user.")
    if not department_id:
        e.append("Select the department to charge.")
    if not (isinstance(allocated_date, date) and isinstance(expiry_date, date)):
        e.append("Enter the allocation start and expiry dates.")
    elif expiry_date <= allocated_date:
        e.append("The expiry date must be after the allocation date.")
    _raise(e)


def validate_renewal(license_id, new_end_date, cost):
    e = []
    if not license_id:
        e.append("Select a license.")
    if not isinstance(new_end_date, date):
        e.append("Enter the new end date.")
    if cost is None or cost <= 0:
        e.append("Renewal cost must be greater than zero.")
    elif cost > 100_000_000:
        e.append("Renewal cost looks too large. Check the amount.")
    _raise(e)


def validate_fields(values, spec):
    """Validate master-data form values against a field spec list."""
    e = []
    for f in spec:
        v = values.get(f["name"])
        label = f["label"]
        if f["required"] and (v is None or v == ""):
            e.append(f"{label} is required.")
            continue
        if v in (None, ""):
            continue
        kind = f["kind"]
        if kind in ("text", "email") and len(str(v)) > f.get("max", 255):
            e.append(f"{label} can't exceed {f.get('max', 255)} characters.")
        if kind == "email" and not EMAIL_RE.match(str(v)):
            e.append(f"{label} must be a valid email address.")
        if kind == "int" and (not isinstance(v, int) or v <= 0):
            e.append(f"{label} must be a whole number greater than zero.")
    _raise(e)
