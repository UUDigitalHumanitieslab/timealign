<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="p | head">
    <td>
    <xsl:for-each select="s">
        <xsl:for-each select="w">
            <xsl:choose>
            <xsl:when test="@fragment-pk">
                <a>
                    <xsl:attribute name="href">../../show/<xsl:value-of select="@fragment-pk" /></xsl:attribute>
                    <xsl:attribute name="title">
                        <xsl:value-of select="@label" />
                    </xsl:attribute>
                    <xsl:attribute name="data-annotation-pk">
                        <xsl:value-of select="@annotation-pk" />
                    </xsl:attribute>
                    <xsl:attribute name="data-xml-id">
                        <xsl:value-of select="@id" />
                    </xsl:attribute>
                    <xsl:attribute name="data-label">
                        <xsl:value-of select="@label" />
                    </xsl:attribute>
                    <xsl:attribute name="style">
                        background-color: <xsl:value-of select="@color" />;
                        opacity: 0.75;
                        color: black;
                        <xsl:if test="@dialog &gt;= 0.5">
                            font-style: italic;
                        </xsl:if>
                    </xsl:attribute>
                    <xsl:value-of select="." />
                </a>
            </xsl:when>
            <xsl:otherwise>
                <span>
                    <xsl:attribute name="data-xml-id">
                        <xsl:value-of select="@id" />
                    </xsl:attribute>
                    <xsl:attribute name="style">
                        <xsl:if test="@dialog &gt;= 0.5">
                            font-style: italic;
                        </xsl:if>
                    </xsl:attribute>
                    <xsl:value-of select="." />
                </span>
            </xsl:otherwise>
            </xsl:choose>
            <xsl:text> </xsl:text>
        </xsl:for-each>
    </xsl:for-each>
    </td>
</xsl:template>
</xsl:stylesheet>
