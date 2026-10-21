# Cursor pagination for ticket lists

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Listing

GET /tickets returns items and next_cursor. Page size defaults to 20 and is capped at 100. next_cursor is opaque and tied to the original filters and sort. There are no page-number offsets. A missing next_cursor means the list is complete.

## Troubleshooting

Pass next_cursor unchanged to fetch the next page with the same filters and sort. Restart pagination if filters change or a cursor returns 400 CURSOR_INVALID. Stop when next_cursor is absent. Do not construct or decode cursor values, and do not combine a cursor with different filters.
