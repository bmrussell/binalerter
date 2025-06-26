#!/usr/bin/env pwsh

param([string]$PostCode = "SN6 6NX", $ApiUrl="https://ilforms.wiltshire.gov.uk/WasteCollectionDays/AddressList", $CollectionUrl="https://ilforms.wiltshire.gov.uk/WasteCollectionDays/CollectionList")

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



$postParams = @{Postcode=$PostCode;Month=(Get-Date).Month;Year=(Get-Date).Year}
$result = Invoke-WebRequest -Uri $ApiUrl -Method POST -Body $postParams
$resultJson = ConvertFrom-Json -InputObject $result

$addressId = $resultJson.Model.PostcodeAddresses[0].UPRN
$postParams.Add('Uprn', $addressId)

$postParams = @{Postcode=$PostCode;Month=(Get-Date).Month;Year=(Get-Date).Year; Uprn=$addressId}
$result = Invoke-WebRequest -Uri $CollectionUrl -Method POST -Body $postParams

$regex = '<a\s+data-event-id="(?<type>res|pod|cgw)"\s+class="event service-(res|pod|cgw)"\s+data-toggle="[a-z]+"\s+title=""\s+data-original-datetext="([A-Za-z]+)\s+(?<day>[0-9]{1,2})\s(?<month>[A-Za-z]*),\s(?<year>[0-9]{4})"'

# group 1 = pod/res/cgw
# Group 3 = Day name
# Group 4 = Day number
# Group 5 = Month Name
# Group 6 = Year

$collections = @()

$allmatches = ($result.Content | select-string -pattern $regex  -AllMatches)
$nextIndicator = "*"
for ($i = 0; $i -lt $allmatches.matches.count; $i++) {
    $collection = New-Object -TypeName CollectionEvent
    $type = $allmatches.matches[$i].groups['type'].value
    if ($type -eq "cgw" ) {
        $collection.CollectionType = "Garden"
    } elseif ($type -eq "pod" ) {
        $collection.CollectionType = "Cardboard & Glass"
    } elseif ($type -eq "res" ) {
        $collection.CollectionType = "Household"
    } else {
        $collection.CollectionType = "Unknown!"
    }

    $collectionDay = $allmatches.matches[$i].groups['day'].value
    $collectionMonth = $allmatches.matches[$i].groups['month'].value
    $collectionYear = $allmatches.matches[$i].groups['year'].value
    $collection.CollectionDate = [datetime]::parseexact("$($collectionDay)-$($collectionMonth)-$($collectionYear) 07:00", "d-MMMM-yyyy HH:mm", $null)

    if ($collection.CollectionDate -lt (Get-Date)) {
        $collection.CollectionDate = $null
    }

    $collections += $collection
}


$collections


$ProgressPreference = 'Continue'
