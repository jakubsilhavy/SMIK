# smik
import time
import math
from datetime import datetime
from datetime import timedelta
from operator import attrgetter

##### CONFIGURATION ####
# jizdni rad ve formatu
# Name;Code;TimeFrom;TimeTo;Weight
# 1A;101;0;10;3
# program predpoklada oznaceni kontrol cislem a pismenem
# napr. pri razeni kontroluje, zda zavodnik jiz nema spravne orazenou jinou variantu kontroly (jine pismeno)
timetablePath = "timetable.txt"
# vystup z SI configu
readCardPath = "read_smik.csv"
# seznam prihlasenych zavodniku ve formatu
# registracni_cislo;kategorie;cislo_SI;jmeno; licence
# OAV7801;H;2027232;Leštínský Tomáš;C
# program nacita jen kategorii, cislo cipu a jmeno
entryPath = 'entry.txt'
# cas startu 00
startTime = datetime.strptime("17:00:00", "%H:%M:%S")
# cas konce limitu
endTime = datetime.strptime("17:45:00", "%H:%M:%S")
# tolerance razeni v sekundach
PUNCH_TOLERANCE = 5

timetable = {}

# trida pro kontrolu v zavode
class Control:
  def __init__(self, name, code, timeFrom, timeTo, weight):
    self.name = name
    self.code = code
    self.timeFrom = timeFrom
    self.timeTo = timeTo
    self.weight = weight
  
  # vyhodnoceni razeni zavodnika
  # vraci True pokud byla kontrola orazena ve spravnem case s toleranci PUNCH_TOLERANCE (viz configuration)
  def evaluate(self, punchTime):
    return punchTime.seconds <= (int(self.timeTo)*60+PUNCH_TOLERANCE) and punchTime.seconds >= (int(self.timeFrom)*60-PUNCH_TOLERANCE)
  
# trida pro zavodnika
class Runner:
  def __init__(self, siCard):
    self.siCard = siCard
    self.category = self.getEntryInfo(siCard,1)
    self.name = self.getEntryInfo(siCard,3)
    self.validPunch = []
    self.invalidPunch = []
    self.totalTime = None
    self.compareTime = None
    self.penaltyScore = 0
    self.score = 0
    self.reducedScore = 0

  # dle cisla cipu nacte informaci z prihlasek dle zadaneho poradi (index)
  def getEntryInfo(self, siCard, index):
    entryFile = open(entryPath, 'r')
    entryDict = {}
    for line in entryFile:
      entryItems = line.split(';')
      # vytvari slovnik [cislo_cipu, pozadovana_hodnota]
      entryDict[entryItems[2]] = entryItems[index]
    # vraci pozadovanou hodnotu pro zadane cislo cipu
    return entryDict[siCard].strip()

  # prida razeni zavodnikovi
  # prida skore, pokud byla kontrola orazena ve spravnem case
  def addPunch(self, punchControl, punchTime):
    # pokud je kontrola v jizdnim radu
    if punchControl in timetable:
      # nacte informace o kontrole
      control = timetable[punchControl]
      # kontrola, zda jiz nema kontrolu uznanou jako validni (jinou variantu kontroly)
      if not control.name[:-1] in map(lambda control : control.name[:-1], self.validPunch):
        # kontrola razeni kontroly ve spravnem case
        if control.evaluate(punchTime):
          self.validPunch.append(control)
          self.score+=int(control.weight)
        else:
          self.invalidPunch.append(control)
      else:
        self.invalidPunch.append(control)
  
  # zapsani ciloveho razeni vcetne penalizace za prekroceni limitu
  def setFinishTime(self, finishTime):
    self.totalTime = finishTime-startTime
    # kvuli razeni vysledku
    self.compareTime = datetime.strptime("23:00:00", "%H:%M:%S") - self.totalTime
    df = finishTime-endTime
    # prekroceni casoveho limitu => penalizace
    if (not df.days < 0) and (df.seconds > 0):
      penaltyMinutes = int(math.ceil((df.seconds+1)/60.0))
      self.penaltyScore=penaltyMinutes/2.0*(penaltyMinutes+1)

  # vypocet skore po odecteni penalizace
  def computeReducedScore(self):
    self.reducedScore = self.score-self.penaltyScore
    if (self.reducedScore < 0):
      self.reducedScore=0    

  # vypis validniho razeni
  def printPunch(self):
    controlSequence = map(lambda control : control.name, self.validPunch)
    sortedControlSequence = sorted(controlSequence)
    punchToPrint="{};{};{};{};{};{};{};{}".format(self.category, self.siCard, self.name, int(self.reducedScore), self.score, int(self.penaltyScore), self.totalTime, ";".join(sortedControlSequence))
    print(punchToPrint)
    return(punchToPrint)

def getPunchTime(punchTime):
  return datetime.strptime(punchTime.strip(), "%H:%M:%S")

def getTimeFromStart(punchTime):
  return punchTime-startTime

# zpracovani vysledku
def processResult():
  # otevre export s SI Configu
  readCardFile = open(readCardPath, 'r')
  readCardFile.next()
  runners = []

  # pro kazdy radek => pro kazdeho zavodnika
  for line in readCardFile:
    # data z SI Configu - nacitaji se dle poradi sloupcu
    punch = line.strip().split(';')
    # inicializace zavodnika dle cisla cipu
    runner = Runner(punch[2].strip())
    runners.append(runner)
    print(runner.name)
    # nacteni ciloveho casu
    ft = punch[21].strip()
    # orez desetinych mist u sekund u novych cipu
    # pokud na desetinach vterin zalezi, nutno prepsat kod
    if (len(ft) > 8):
      ft = ft[:8]
    finishTime = datetime.strptime(ft, "%H:%M:%S")
    runner.setFinishTime(finishTime)
    print("Cil: {}".format(finishTime-startTime))
    noControls = punch[44]
    # cislo sloupce prvni kontroly v exportu z SI Configu
    FIRST_CONTROL_INDEX = 45
    # nacteni zavodnikovo razeni => pro vsechny orazene kontroly
    for control in range(0,int(noControls),1):
      # nalezne zaznam v exportu z SI Configu
      # kod kontroly
      punchControl = punch[FIRST_CONTROL_INDEX+3*control]
      # absolutni cas razeni kontroly
      punchTime = getPunchTime(punch[FIRST_CONTROL_INDEX+3*control+2])
      # relativni cas razeni kontroly od startu zavodu
      relativePunchTime = getTimeFromStart(punchTime)
      print("{}\t{}".format(punchControl,relativePunchTime))
      runner.addPunch(punchControl,relativePunchTime)
    runner.computeReducedScore()
  # serazeni zavodniku dle kategorie, skore a dosazeneho casu
  sortedRunners = sorted(runners, key=attrgetter('category','reducedScore', 'compareTime'), reverse=True)
  # zapis vysledku
  outF = open("resutls.csv",'w')
  for runner in sortedRunners:
    outF.write(runner.printPunch()+'\n')
  outF.close()

# vytvoreni slovniku pro jizdni rad
def initTimetable():
  readCardFile = open(timetablePath, 'r')
  # skip header
  readCardFile.next()
  for line in readCardFile:
    lineSplit = line.strip().split(';')
    control = Control(*lineSplit)
    timetable[lineSplit[1]] = control
  return timetable

#### spusteni programu
if __name__== "__main__":
  timetable = initTimetable()
  processResult()