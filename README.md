# Amsterdam Diaries Project
Documentation and files for Amsterdam Diaries Project

- [Amsterdam Diaries Project](#amsterdam-diaries-project)
  - [Project Description](#project-description)
  - [Data](#data)
  - [Annotation](#annotation)
    - [Transkribus](#transkribus)
      - [Structural markup (images + text regions and lines)](#structural-markup-images--text-regions-and-lines)
      - [Textual markup](#textual-markup)
      - [Tags (entities)](#tags-entities)


## Project Description


## Data

### Source data

### Data model
```plantuml

@startuml
hide circle

'Classes

class Thing as "Thing (schema:Thing)" {
}

class Archive as "Archive (schema:ArchiveOrganization)" {
--
name (schema:name)
}

class Collection as "Collection (schema:Collection)" #wheat {
* URI
--
name (schema:name)

}

package Diaries {

class Diary as "Diary (schema:Book)" #salmon {
* URI
--
name (schema:name)
author (schema:author)
date (schema:temporalCoverage)
}

' Or Manuscript if everything is written?
class Entry as "Entry (schema:CreativeWork)" #thistle {
* URI
--
name (schema:name)
date (schema:temporalCoverage)
text (schema:text)
}

class Scan as "Scan (schema:ImageObject)" #lightgreen {
* URI
--
name (schema:name)
}

}

package "External data" {

class Person as "Person (schema:Person)" #lightblue {
* URI
--

}

class PersonName as "PersonName (pnv:PersonName)" {
--
givenName (pnv:givenName)
surnamePrefix (pnv:surnamePrefix)
baseSurname (pnv:baseSurname)
literalName (pnv:literalName)
}

class Location as "Location (schema:Place)" #lightblue{
* URI
--

}

class Concept as "Concept (skos:Concept)" #lightblue {
* URI
--

}

}

' Web Annotation stuff
package WADM as "Annotation" {

class Annotation as "Annotation (oa:Annotation)" #silver {
* URI
--
body (oa:hasBody)
target (oa:hasTarget)
}

class SpecificResource as "SpecificResource (oa:SpecificResource)" #silver {
--
purpose (oa:hasPurpose)
}

class TextualBody as "TextualBody (oa:TextualBody)" #silver {
--
purpose (oa:hasPurpose)
}

class Selector as "Selector (oa:Selector)" #silver {
--
conformsTo (dcterms:conformsTo)
value (rdf:value)

}

}





'Relations

Collection -l-> Archive: schema:holdingArchive

Diary -u--> Collection: schema:isPartOf
Entry -u--> Diary: schema:isPartOf

Entry --|> Thing
Entry ---> Thing: schema:about
Entry --l-> Scan: schema:image

Scan --|> Thing

Person --u-|> Thing
Location --u-|> Thing
Concept --u-|> Thing

Person --> PersonName: pnv:hasName

Annotation ---> TextualBody: oa:hasBody
Annotation ---> SpecificResource: oa:hasBody
Annotation ---> SpecificResource: oa:hasTarget

SpecificResource ---> Thing: oa:hasSource
SpecificResource ---> Selector: oa:hasSelector

```

## Annotation

### Transkribus
We load the data in Transkribus and run a basic layout analysis over the pages using their `Transkribus LA` model.
#### Structural markup (images + text regions and lines)

* Visual
* Header
* Heading
* Paragraph
* Page number

#### Textual markup

* Strikethrough

#### Tags (entities)

* Date
* Person
* Place



