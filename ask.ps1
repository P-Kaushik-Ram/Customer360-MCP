param([string]$Question)

$ENDPOINT = "https://urkdocl-wj23271.snowflakecomputing.com/api/v2/databases/CUSTOMER_360/schemas/SILVER/mcp-servers/CUSTOMER360_MCP"
$PAT = $env:SNOWFLAKE_PAT

$body = @{
  jsonrpc = "2.0"
  id = 1
  method = "tools/call"
  params = @{
    name = "ask_customer360"
    arguments = @{ message = $Question }
  }
} | ConvertTo-Json -Depth 10

$resp = Invoke-RestMethod -Uri $ENDPOINT -Method Post -Headers @{
  "Authorization" = "Bearer $PAT"
  "Accept" = "application/json"
} -ContentType "application/json" -Body $body

$inner = $resp.result.content[0].text | ConvertFrom-Json

foreach ($item in $inner) {
    if ($item.text)      { Write-Host "`n$($item.text)`n" -ForegroundColor Cyan }
    if ($item.statement) {
        Write-Host "Running generated SQL...`n" -ForegroundColor DarkGray
        snow sql -q $item.statement -c customer360
    }
}