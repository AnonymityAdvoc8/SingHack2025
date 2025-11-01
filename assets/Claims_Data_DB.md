# Database Information

## JDBC URL
```
jdbc:postgresql://hackathon-db.ceqjfmi6jhdd.ap-southeast-1.rds.amazonaws.com:5432/hackathon_db
```

## Connection Details
- **Host:** hackathon-db.ceqjfmi6jhdd.ap-southeast-1.rds.amazonaws.com
- **Port:** 5432
- **Database:** hackathon_db
- **Username:** hackathon_user
- **Password:** Hackathon2025!

---

## Database Schema

### Schema Name
`hackathon`

### Table Name
`claims`

### Description
MSIG travel insurance claims data

### Table Structure

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| claim_number | VARCHAR(50) | Unique claim identifier (Primary Key) |
| product_category | VARCHAR(100) | Product classification |
| product_name | VARCHAR(200) | Specific product name |
| claim_status | VARCHAR(100) | Current status of claim |
| accident_date | DATE | Date when incident occurred |
| report_date | DATE | Date when claim was reported |
| closed_date | DATE | Date when claim was closed (NULL if open) |
| destination | VARCHAR(100) | Travel destination |
| claim_type | VARCHAR(100) | Type of claim |
| cause_of_loss | VARCHAR(100) | Root cause of loss |
| loss_type | VARCHAR(100) | Detailed loss category |
| gross_incurred | DECIMAL(10,2) | Total claim amount before reinsurance (SGD) |
| gross_paid | DECIMAL(10,2) | Amount paid before reinsurance (SGD) |
| gross_reserve | DECIMAL(10,2) | Amount reserved before reinsurance (SGD) |
| net_incurred | DECIMAL(10,2) | Total claim amount after reinsurance (SGD) |
| net_paid | DECIMAL(10,2) | Amount paid after reinsurance (SGD) |
| net_reserve | DECIMAL(10,2) | Amount reserved after reinsurance (SGD) |
