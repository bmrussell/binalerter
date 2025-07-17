#!/usr/bin/env pwsh

param([string]$PostCode = "SN6 6NX", $ApiUrl = "https://ilforms.wiltshire.gov.uk/WasteCollectionDays/AddressList", $CollectionUrl = "https://ilforms.wiltshire.gov.uk/WasteCollectionDays/CollectionList")

$ProgressPreference = 'SilentlyContinue'

class CollectionEvent {
    [string]$CollectionType
    [Nullable[datetime]]$CollectionDate
}

$uri = 'https://ilforms.wiltshire.gov.uk/WasteCollectionDays/index'
$headers = New-Object "System.Collections.Generic.Dictionary[[String],[String]]"
$headers.Add('Host', 'ilforms.wiltshire.gov.uk')
$headers.Add('Connection', 'keep-alive')
$headers.Add('DNT', '1')
$headers.Add('Upgrade-Insecure-Requests', '1')
$headers.Add('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36')
$headers.Add('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
$headers.Add('Sec-Fetch-Site', 'none')
$headers.Add('Sec-Fetch-Mode', 'navigate')
$headers.Add('Sec-Fetch-Dest', 'document')
$headers.Add('Accept-Encoding', 'gzip, deflate, br')
$headers.Add('Accept-Language', 'en-GB,en;q=0.9,en-US;q=0.8')
$result = Invoke-WebRequest -Uri $uri -Headers $headers



$postParams = @{Postcode = $PostCode; Month = (Get-Date).Month; Year = (Get-Date).Year }
$result = Invoke-WebRequest -Uri $ApiUrl -Method POST -Body $postParams
$resultJson = ConvertFrom-Json -InputObject $result

$addressId = $resultJson.Model.PostcodeAddresses[0].UPRN
$postParams.Add('Uprn', $addressId)

$postParams = @{Postcode = $PostCode; Month = (Get-Date).Month; Year = (Get-Date).Year; Uprn = $addressId }
$result = Invoke-WebRequest -Uri $CollectionUrl -Method POST -Body $postParams


$html = $result.Content
# Patterns to extract each part of the date
$regexDayNames = '<span\s+class="card-collection-day">\s*([A-Za-z]+)\s*</span>'
$regexDayNumbers = '<span class="card-collection-date">\s*(\d{1,2})\s*</span>'
$regexMonthYears = '<span class="card-collection-month">\s*(.*?)\s*</span>'
$regexCollection = '<li class="collection-type-[^"]+">\s*(.*?)\s*</li>'

# Extract each component of the date
$daynames = [regex]::Matches($html, $regexDayNames) | ForEach-Object { $_.Groups[1].Value.Trim() }
$daynumbers = [regex]::Matches($html, $regexDayNumbers) | ForEach-Object { $_.Groups[1].Value.Trim() }
$monthyears = [regex]::Matches($html, $regexMonthYears) | ForEach-Object { $_.Groups[1].Value.Trim() }
$collections = [regex]::Matches($html, $regexCollection) | ForEach-Object { $_.Groups[1].Value.Trim() }

$collectionEvents = for ($i = 0; $i -lt $collections.Count; $i++) {
    [CollectionEvent]@{
        CollectionType = $collections[$i]
        CollectionDate = [datetime]::ParseExact("$($daynumbers[$i]) $($monthyears[$i])", "d MMMM yyyy", $null)
    }
}
#$collectionEvents

#$collectionEvents  | Where-Object { $_.CollectionDate -gt (Get-Date).Date } 



$collectionEvents |
Where-Object { $_.CollectionDate -gt (Get-Date).Date } |
Select-Object CollectionType, @{Name = 'CollectionDate' 
    Expression  = {
        $date = $_.CollectionDate
        $formattedDate = $date.ToString('dd MMMM yyyy')
        if ($date.Date -eq (Get-Date).AddDays(1).Date) {
            "$formattedDate*"
        }
        else {
            $formattedDate
        }
    }    
        
}

