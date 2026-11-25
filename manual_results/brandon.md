\# FID-3 Update Product — Manual Test Results



\*\*Tester:\*\* Brandon Dixon  

\*\*Date:\*\* 25 November 2026  

\*\*Branch:\*\* brandon-fid3  

\*\*Feature:\*\* FID-3 Update Product



\## Automated Testing



Command: `python -m unittest discover -s tests -t . -v`



\- Total tests: 87

\- Passed: 85

\- Skipped: 2

\- Failed: 0

\- Result: OK (skipped=2)



All eleven FID-3 automated tests passed.



\## Manual Test Results



| Test | Result | What happened |

|---|---|---|

| TS3.1 | PASS | Logged in as manager and successfully opened the Update Product window. |

| TS3.2 | PASS (cashier check) | Logged in as cashier and attempted to edit a product. The application displayed an Access Denied message. |

| TS3.3 | PASS | Rice 5kg displayed its correct saved name and low-stock threshold of 5. |

| TS3.4 | PASS | Rice 5kg showed a blank expiry-date field because no expiry date was originally saved. |

| TS3.5 | PASS | An empty product name was rejected with the message "Product name is required." |

| TS3.6 | PASS | Negative and non-numeric thresholds were rejected. A threshold of 0 was accepted. An invalid expiry date was rejected. |

| TS3.7 | PASS | Updated the product name and low-stock threshold. Confirmation appeared and changes were saved successfully. |

| TS3.8 | PARTIAL | Updating Rice 5kg's expiry date to 2026-12-10 made it appear in nearing-expiry notifications with 4 units and 15 days remaining. Separate product search was not tested because FID-7 is not implemented. |

| TS3.9 | PASS (cancellation); automated save-failure check | Selecting No at the confirmation prompt left the product unchanged. The failed-save scenario was covered by automated testing. |

| TS3.10 | PASS (automated only) | The FID-3 automated test confirmed successful updates create audit-log entries. The log was not manually inspected. |

| TS3.11 | PASS (automated only) | The FID-3 automated test confirmed rejected or cancelled updates do not create audit-log entries. |



\## GUI Test — TC-GUI-3



\*\*Result: PASS for manually checked GUI behavior\*\*



Verified:

\- The Update Product window opens.

\- Existing product details display correctly.

\- A confirmation pop-up appears before saving.

\- Valid changes are saved and displayed.

\- Cancelling the confirmation leaves the product unchanged.

\- Empty names, invalid thresholds, invalid dates and duplicate names are rejected.

\- Past expiry dates are accepted when editing.

\- An unauthorized cashier cannot edit products.



\## Observations



1\. The cashier can see the Edit button, but clicking it correctly displays Access Denied.

2\. The rightmost low-stock column was partially cut off at the displayed window size.

3\. The automated test suite passed with no failures.



\## Conclusion



FID-3 Update Product passed the manual GUI checks performed and all eleven automated FID-3 tests. The outstanding portions and automated-only checks are identified above.

