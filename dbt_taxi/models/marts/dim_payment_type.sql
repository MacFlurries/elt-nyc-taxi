-- Sumber label: TLC Yellow Taxi data dictionary, 18 Maret 2025
select 0 as payment_type_id, 'Flex Fare trip' as payment_type_name
union all select 1, 'Credit card'
union all select 2, 'Cash'
union all select 3, 'No charge'
union all select 4, 'Dispute'
union all select 5, 'Unknown'
union all select 6, 'Voided trip'