from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import (
    BIGINT,
    CHAR,
    DATETIME,
    INTEGER,
    TEXT,
    TINYINT,
    VARCHAR,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ConfigRefsets(Base):
    __tablename__ = "config_Refsets"
    refsetId = Column(BIGINT(), primary_key=True, nullable=False)
    refsetType = Column(VARCHAR(length=60), nullable=False)


class SnapRelationship(Base):
    __tablename__ = "relationship"
    id = Column(Numeric(18, 0), primary_key=True, nullable=False)
    effectivetime = Column(DateTime, primary_key=True, nullable=False)
    active = Column(Boolean, nullable=False)
    moduleid = Column(Numeric(18, 0), nullable=False)
    sourceid = Column(Numeric(18, 0), nullable=False)
    destinationid = Column(Numeric(18, 0), nullable=False)
    relationshipgroup = Column(Integer, nullable=False)
    typeid = Column(Numeric(18, 0), nullable=False)
    characteristictypeid = Column(Numeric(18, 0), nullable=False)
    modifierid = Column(Numeric(18, 0), nullable=False)


class ConfigLanguage(Base):
    __tablename__ = "config_language"
    id = Column(BIGINT(), primary_key=True, nullable=False)
    prefix = Column(
        VARCHAR(length=5),
    )
    name = Column(VARCHAR(length=255), nullable=False)


class ConfigResultsets(Base):
    __tablename__ = "config_resultsets"
    setId = Column(VARCHAR(length=12), primary_key=True, nullable=False)
    conceptId = Column(BIGINT(), primary_key=True, nullable=False)


class ConfigSettings(Base):
    __tablename__ = "config_settings"
    id = Column(TINYINT(display_width=1), primary_key=True, nullable=False)
    languageId = Column(
        BIGINT(),
    )
    languageName = Column(VARCHAR(length=255), nullable=False)
    snapshotTime = Column(DATETIME(), nullable=False)
    deltaStartTime = Column(DATETIME(), nullable=False)
    deltaEndTime = Column(DATETIME(), nullable=False)


class FullConcept(Base):
    __tablename__ = "full_concept"
    id = Column(BIGINT(), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    definitionStatusId = Column(BIGINT(), nullable=False)


class FullDescription(Base):
    __tablename__ = "full_description"
    id = Column(BIGINT(), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    conceptId = Column(BIGINT(), nullable=False)
    languageCode = Column(VARCHAR(length=3), nullable=False)
    typeId = Column(BIGINT(), nullable=False)
    term = Column(TEXT(), nullable=False)
    caseSignificanceId = Column(BIGINT(), nullable=False)


class FullRefsetAssociation(Base):
    __tablename__ = "full_refset_Association"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    targetComponentId = Column(BIGINT(), nullable=False)


class FullRefsetAttributevalue(Base):
    __tablename__ = "full_refset_AttributeValue"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    valueId = Column(BIGINT(), nullable=False)


class FullRefsetDescriptiontype(Base):
    __tablename__ = "full_refset_DescriptionType"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    descriptionFormat = Column(BIGINT(), nullable=False)
    descriptionLength = Column(INTEGER(), nullable=False)


class FullRefsetExtendedmap(Base):
    __tablename__ = "full_refset_ExtendedMap"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    mapGroup = Column(INTEGER(), nullable=False)
    mapPriority = Column(INTEGER(), nullable=False)
    mapRule = Column(TEXT(), nullable=False)
    mapAdvice = Column(TEXT(), nullable=False)
    mapTarget = Column(
        VARCHAR(charset="utf8mb4", collation="utf8mb4_bin", length=200), nullable=False
    )
    correlationId = Column(BIGINT(), nullable=False)
    mapCategoryId = Column(BIGINT(), nullable=False)


class FullRefsetLanguage(Base):
    __tablename__ = "full_refset_Language"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    acceptabilityId = Column(BIGINT(), nullable=False)


class FullRefsetMrcmattributedomain(Base):
    __tablename__ = "full_refset_MRCMAttributeDomain"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    domainId = Column(BIGINT(), nullable=False)
    grouped = Column(INTEGER(), nullable=False)
    attributeCardinality = Column(VARCHAR(length=12), nullable=False)
    attributeInGroupCardinality = Column(VARCHAR(length=12), nullable=False)
    ruleStrengthId = Column(BIGINT(), nullable=False)
    contentTypeId = Column(BIGINT(), nullable=False)


class FullRefsetMrcmattributerange(Base):
    __tablename__ = "full_refset_MRCMAttributeRange"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    rangeConstraint = Column(TEXT(), nullable=False)
    attributeRule = Column(TEXT(), nullable=False)
    ruleStrengthId = Column(BIGINT(), nullable=False)
    contentTypeId = Column(BIGINT(), nullable=False)


class FullRefsetMrcmdomain(Base):
    __tablename__ = "full_refset_MRCMDomain"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    domainConstraint = Column(TEXT(), nullable=False)
    parentDomain = Column(TEXT(), nullable=False)
    proximalPrimitiveConstraint = Column(TEXT(), nullable=False)
    proximalPrimitiveRefinement = Column(TEXT(), nullable=False)
    domainTemplateForPrecoordination = Column(TEXT(), nullable=False)
    domainTemplateForPostcoordination = Column(TEXT(), nullable=False)
    guideURL = Column(TEXT(), nullable=False)


class FullRefsetMrcmmodulescope(Base):
    __tablename__ = "full_refset_MRCMModuleScope"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    mrcmRuleRefsetId = Column(BIGINT(), nullable=False)


class FullRefsetModuledependency(Base):
    __tablename__ = "full_refset_ModuleDependency"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    sourceEffectiveTime = Column(DATETIME(), nullable=False)
    targetEffectiveTime = Column(DATETIME(), nullable=False)


class FullRefsetOwlexpression(Base):
    __tablename__ = "full_refset_OWLExpression"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    owlExpression = Column(TEXT(), nullable=False)


class FullRefsetRefsetdescriptor(Base):
    __tablename__ = "full_refset_RefsetDescriptor"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    attributeDescription = Column(BIGINT(), nullable=False)
    attributeType = Column(BIGINT(), nullable=False)
    attributeOrder = Column(INTEGER(), nullable=False)


class FullRefsetSimple(Base):
    __tablename__ = "full_refset_Simple"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)


class FullRefsetSimplemap(Base):
    __tablename__ = "full_refset_SimpleMap"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    mapTarget = Column(
        VARCHAR(charset="utf8mb4", collation="utf8mb4_bin", length=200), nullable=False
    )


class FullRelationship(Base):
    __tablename__ = "full_relationship"
    id = Column(BIGINT(), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    sourceId = Column(BIGINT(), nullable=False)
    destinationId = Column(BIGINT(), nullable=False)
    relationshipGroup = Column(INTEGER(), nullable=False)
    typeId = Column(BIGINT(), nullable=False)
    characteristicTypeId = Column(BIGINT(), nullable=False)
    modifierId = Column(BIGINT(), nullable=False)


class SnapConcept(Base):
    __tablename__ = "snap_concept"
    id = Column(BIGINT(), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    definitionStatusId = Column(BIGINT(), nullable=False)


class SnapDescription(Base):
    __tablename__ = "description"
    id = Column(Numeric(18, 0), primary_key=True, nullable=False)
    effectivetime = Column(DateTime, primary_key=True, nullable=False)
    active = Column(Boolean, nullable=False)
    moduleid = Column(Numeric(18, 0), nullable=False)
    conceptid = Column(Numeric(18, 0), nullable=False)
    languagecode = Column(String(3), nullable=False)
    typeid = Column(Numeric(18, 0), nullable=False)
    term = Column(Text, nullable=False)
    casesignificanceid = Column(Numeric(18, 0), nullable=False)


class SnapProximalPrimitives(Base):
    __tablename__ = "snap_proximal_primitives"
    subtypeId = Column(BIGINT(), primary_key=True, nullable=False)
    supertypeId = Column(BIGINT(), primary_key=True, nullable=False)


class SnapRefsetAssociation(Base):
    __tablename__ = "snap_refset_Association"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    targetComponentId = Column(BIGINT(), nullable=False)


class SnapRefsetAttributevalue(Base):
    __tablename__ = "snap_refset_AttributeValue"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    valueId = Column(BIGINT(), nullable=False)


class SnapRefsetDescriptiontype(Base):
    __tablename__ = "snap_refset_DescriptionType"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    descriptionFormat = Column(BIGINT(), nullable=False)
    descriptionLength = Column(INTEGER(), nullable=False)


class SnapRefsetExtendedmap(Base):
    __tablename__ = "snap_refset_ExtendedMap"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    mapGroup = Column(INTEGER(), nullable=False)
    mapPriority = Column(INTEGER(), nullable=False)
    mapRule = Column(TEXT(), nullable=False)
    mapAdvice = Column(TEXT(), nullable=False)
    mapTarget = Column(
        VARCHAR(charset="utf8mb4", collation="utf8mb4_bin", length=200), nullable=False
    )
    correlationId = Column(BIGINT(), nullable=False)
    mapCategoryId = Column(BIGINT(), nullable=False)


class SnapRefsetLanguage(Base):
    __tablename__ = "snap_refset_Language"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    acceptabilityId = Column(BIGINT(), nullable=False)


class SnapRefsetMrcmattributedomain(Base):
    __tablename__ = "snap_refset_MRCMAttributeDomain"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    domainId = Column(BIGINT(), nullable=False)
    grouped = Column(INTEGER(), nullable=False)
    attributeCardinality = Column(VARCHAR(length=12), nullable=False)
    attributeInGroupCardinality = Column(VARCHAR(length=12), nullable=False)
    ruleStrengthId = Column(BIGINT(), nullable=False)
    contentTypeId = Column(BIGINT(), nullable=False)


class SnapRefsetMrcmattributerange(Base):
    __tablename__ = "snap_refset_MRCMAttributeRange"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    rangeConstraint = Column(TEXT(), nullable=False)
    attributeRule = Column(TEXT(), nullable=False)
    ruleStrengthId = Column(BIGINT(), nullable=False)
    contentTypeId = Column(BIGINT(), nullable=False)


class SnapRefsetMrcmdomain(Base):
    __tablename__ = "snap_refset_MRCMDomain"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    domainConstraint = Column(TEXT(), nullable=False)
    parentDomain = Column(TEXT(), nullable=False)
    proximalPrimitiveConstraint = Column(TEXT(), nullable=False)
    proximalPrimitiveRefinement = Column(TEXT(), nullable=False)
    domainTemplateForPrecoordination = Column(TEXT(), nullable=False)
    domainTemplateForPostcoordination = Column(TEXT(), nullable=False)
    guideURL = Column(TEXT(), nullable=False)


class SnapRefsetMrcmmodulescope(Base):
    __tablename__ = "snap_refset_MRCMModuleScope"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    mrcmRuleRefsetId = Column(BIGINT(), nullable=False)


class SnapRefsetModuledependency(Base):
    __tablename__ = "snap_refset_ModuleDependency"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    sourceEffectiveTime = Column(DATETIME(), nullable=False)
    targetEffectiveTime = Column(DATETIME(), nullable=False)


class SnapRefsetOwlexpression(Base):
    __tablename__ = "snap_refset_OWLExpression"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    owlExpression = Column(TEXT(), nullable=False)


class SnapRefsetRefsetdescriptor(Base):
    __tablename__ = "snap_refset_RefsetDescriptor"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    attributeDescription = Column(BIGINT(), nullable=False)
    attributeType = Column(BIGINT(), nullable=False)
    attributeOrder = Column(INTEGER(), nullable=False)


class SnapRefsetSimple(Base):
    __tablename__ = "snap_refset_Simple"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)


class SnapRefsetSimplemap(Base):
    __tablename__ = "snap_refset_SimpleMap"
    id = Column(CHAR(length=36), primary_key=True, nullable=False)
    effectiveTime = Column(DATETIME(), primary_key=True, nullable=False)
    active = Column(TINYINT(), nullable=False)
    moduleId = Column(BIGINT(), nullable=False)
    refsetId = Column(BIGINT(), nullable=False)
    referencedComponentId = Column(BIGINT(), nullable=False)
    mapTarget = Column(
        VARCHAR(charset="utf8mb4", collation="utf8mb4_bin", length=200), nullable=False
    )


class SnapTransclose(Base):
    __tablename__ = "snap_transclose"
    subtypeId = Column(BIGINT(), primary_key=True, nullable=False)
    supertypeId = Column(BIGINT(), primary_key=True, nullable=False)
