# SMIK

Na vstupu skript vyžaduje:

Jízdní řád ve formátu:# Name;Code;TimeFrom;TimeTo;Weight# 1A;101;0;10;3

Přihlášky závodníků ve formátu:# registracni_cislo;kategorie;cislo_SI;jmeno; licence# OAV7801;H;2027232;Leštínský Tomáš;C(program načítá jen kategorii, číslo čipu a jméno)

A ražení závodníků jako export z programu SportIdent Config+ do CSV.Vyčítá se tedy v programu SportIdent Config+ v režimu "Read SI cards". Až budou vyčteni všichni závodníci, tak se provede export do CSV a spustí se Python skript, který zpracuje výsledky.

Přikládám i data z Třemošné.
