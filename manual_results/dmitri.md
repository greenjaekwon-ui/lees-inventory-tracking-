Manual test results: D'mitri Smith



Date: 24/11/2026

Features: FID-10 Record damaged products (and FID-8 status checks)

Role used: warehouse (cashier for TS-10.1B)



| Test | What I tried | Result |

|---|---|---|

| TS10.1A | Warehouse and manager opened the Record damage form | PASS |

| TS10.1B | Cashier tried to access the form | PASS |

| TS10.2A | Entered product, quantity, reason and note; values kept until submission | PASS |

| TS10.2B | Submitted with the note left blank | PASS |

| TS10.3A | No product or no reason selected | PASS |

| TS10.3B | Quantity negative, decimal, non-numeric or 0 rejected; 1 accepted | PASS |

| TS10.3C | Quantity above current rejected; equal to current accepted | PASS |

| TS10.3D | Entry for a product with no In Stock units rejected | PASS |

| TS10.3E | Note of 200 characters accepted; 201 rejected | PASS |

| TS10.4A | Recorded 3 damaged of 10; quantity changed to 7 | PASS |

| TS10.4B | Rejected entry left the quantity unchanged | PASS |

| TS10.4C | Searched within 2 seconds of saving; reduced quantity shown | PASS |

| TS10.5A | Recorded damage for all 4 of 4; status Damaged, quantity 0 | PASS |

| TS10.5B | Recorded 1 damaged of 4; status In Stock, quantity 3 | PASS |

| TS10.6A | Checked the damage record fields | FAIL: failed to show the damage record showing the different fields |

| TS10.6B | Rejected entry created no damage record | PASS |

| TS10.7A | Confirmation message after a successful save | PASS |

| TS10.7B | Failed save (database unavailable) | PASS |

| TC-TS-10.2A | Warehouse: quantity 2, reason, note "wet pallet", switched tabs and back | PASS |

| TC-TS-10.7A | Recorded a valid damaged quantity; pop-up shown | PASS |



Failure to report to the group: TS10.6A, the app does not show the damage record with its fields (product, quantity, reason, note, date and time, username).



