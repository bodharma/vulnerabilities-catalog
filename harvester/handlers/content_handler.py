from xml.sax.handler import ContentHandler


class CWEHandler(ContentHandler):
    def __init__(self):
        self.cwe = []
        self.description_tag = False
        self.extend_description_tag = False
        self.category_tag = False
        self.weakness_tag = False
        self.weakness_relationships_tag = False
        self.category_relationships_tag = False

        self.potential_mitigations = False
        self.observed_examples = False
        self.detection_methods = False
        self.alternate_terms = False

    def startElement(self, name, attrs):
        if name == "Weakness":
            self.weakness_tag = True
            self.statement = ""
            self.weaknessabs = attrs.get("Abstraction")
            self.name = attrs.get("Name")
            self.idname = attrs.get("ID")
            self.status = attrs.get("Status")
            if not self.name.startswith("DEPRECATED"):
                self.cwe.append(
                    {
                        "name": self.name,
                        "id": self.idname,
                        "status": self.status,
                        "weaknessabs": self.weaknessabs,
                    }
                )

        elif name == "Category":
            self.category_tag = True
            self.category_name = attrs.get("Name")
            self.category_id = attrs.get("ID")
            self.category_status = attrs.get("Status")
            if not self.category_name.startswith("DEPRECATED"):
                self.cwe.append(
                    {
                        "name": self.category_name,
                        "id": self.category_id,
                        "status": self.category_status,
                        "weaknessabs": "Category",
                    }
                )

        elif name == "Observed_Examples":
            self.observed_examples = True

        elif name == "Potential_Mitigations":
            self.potential_mitigations = True

        elif name == "Detection_Methods":
            self.detection_methods = True

        elif name == "Alternate_Terms":
            self.alternate_terms = True

        elif (
            name == "Description"
            and self.weakness_tag
            and not self.potential_mitigations
            and not self.observed_examples
            and not self.detection_methods
            and not self.alternate_terms
        ):
            self.description_tag = True
            self.description = ""

        elif name == "Summary" and self.category_tag:
            self.description_tag = True
            self.description = ""

        elif name == "Relationships" and self.category_tag:
            self.category_relationships_tag = True
            self.relationships = []

        elif name == "Related_Weaknesses" and self.weakness_tag:
            self.weakness_relationships_tag = True
            self.relationships = []

        elif name == "Related_Weakness" and self.weakness_relationships_tag:
            self.relationships.append(attrs.get("CWE_ID"))

        elif name == "Has_Member" and self.category_relationships_tag:
            self.relationships.append(attrs.get("CWE_ID"))

    def characters(self, ch):
        if self.description_tag:
            self.description += ch.replace("       ", "")

    def endElement(self, name):
        if (
            name == "Description"
            and self.weakness_tag
            and not self.observed_examples
            and not self.potential_mitigations
            and not self.detection_methods
            and not self.alternate_terms
        ):
            self.description_tag = False
            self.description = self.description
            self.cwe[-1]["Description"] = self.description.replace("\n", "")
        if name == "Summary" and self.category_tag:
            self.description_tag = False
            self.description = self.description
            self.cwe[-1]["Description"] = self.description.replace("\n", "")
        elif name == "Weakness" and self.weakness_tag:
            self.weakness_tag = False
        elif name == "Category" and self.category_tag:
            self.category_tag = False

        elif name == "Related_Weaknesses" and self.weakness_tag:
            self.weakness_relationships_tag = False
            self.cwe[-1]["related_weaknesses"] = self.relationships

        elif name == "Relationships" and self.category_tag:
            self.category_relationships_tag = False
            self.cwe[-1]["relationships"] = self.relationships

        elif name == "Observed_Examples":
            self.observed_examples = False

        elif name == "Potential_Mitigations":
            self.potential_mitigations = False

        elif name == "Detection_Methods":
            self.detection_methods = False

        elif name == "Alternate_Terms":
            self.alternate_terms = False
