$resolver = New-Object System.Xml.Resolvers.XmlPreloadedResolver
$svgDtdUri = $resolver.ResolveUri("http://www.w3.org/Graphics/SVG/1.1/DTD/", "svg11.dtd")
$svgDtd = Get-Content (Join-Path $PSScriptRoot "svg11.dtd")
$resolver.Add($svgDtdUri, $svgDtd)

function Import-Svg([string]$svgFile)
{
    $svgDOM = New-Object System.Xml.XmlDocument
    $settings = New-Object System.Xml.XmlReaderSettings
    $settings.XmlResolver = $resolver
    $settings.MaxCharactersFromEntities = 0;
    $settings.DtdProcessing = [System.Xml.DtdProcessing]::Parse
    $textReader = [System.IO.File]::OpenText($svgFile)
    $xmlReader = [System.Xml.XmlReader]::Create($textReader, $settings)
    try {
        $svgDOM.Load($xmlReader)
    }
    finally {
        $xmlReader.Close()
        $textReader.Close()
    }
    return $svgDOM
}

function Convert-Svg([string]$svgFile)
{
    $svgDOM = Import-Svg $svgFile
    $namespaceURI = $svgDOM.DocumentElement.NamespaceURI
    $nsmgr = New-Object System.Xml.XmlNamespaceManager($svgDOM.NameTable)
    $nsmgr.AddNamespace("svg", $namespaceURI)

    # set transparent background
    $svgDOM.svg.rect.style = "fill:none;"

    # set responsive text style
    $svgStyle = $svgDOM.CreateElement("style", $namespaceURI)
    $svgStyle.InnerText = "text { fill: #000; } @media (prefers-color-scheme: dark) { text { fill: #eee; } }"
    [void]$svgDOM.SelectSingleNode("/svg:svg", $nsmgr).PrependChild($svgStyle)

    # remove default text style from all text nodes
    foreach ($textElement in $svgDOM.SelectNodes("//svg:text", $nsmgr)) {
        $textElement.style = $textElement.style.replace("fill:rgb(0,0,0);", "")
    }

    $svgDOM.Save($svgFile)
}