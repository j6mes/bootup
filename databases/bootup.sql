
-- Table: Country
CREATE TABLE Country ( 
    Code CHAR( 3 )      PRIMARY KEY
                        NOT NULL,
    Name VARCHAR( 60 )  NOT NULL 
);


-- Table: User
CREATE TABLE User ( 
    IdUser      INTEGER         PRIMARY KEY AUTOINCREMENT
                                NOT NULL,
    Username    VARCHAR( 60 )   NOT NULL
                                UNIQUE,
    RealName    VARCHAR( 200 )  NOT NULL,
    DateOfBirth DATE            NOT NULL 
);


-- Table: Address
CREATE TABLE Address ( 
    IdAddress   INTEGER         PRIMARY KEY AUTOINCREMENT
                                NOT NULL,
    Street      VARCHAR( 100 )  NOT NULL,
    City        VARCHAR( 100 )  NOT NULL,
    PostCode    CHAR( 8 )       NOT NULL,
    CountryCode CHAR( 3 )       NOT NULL
                                REFERENCES Country ( Code ) ON DELETE RESTRICT
                                                            ON UPDATE CASCADE,
    UserId      INTEGER         NOT NULL
                                REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                           ON UPDATE CASCADE 
);


-- Table: Card
CREATE TABLE Card ( 
    IdCard    INTEGER     PRIMARY KEY AUTOINCREMENT
                          NOT NULL,
    Number    CHAR( 12 )  NOT NULL,
    Pin       CHAR( 3 )   NOT NULL,
    ExpDate   DATE        NOT NULL,
    AddressId INTEGER     NOT NULL
                          REFERENCES Address ( IdAddress ) ON DELETE CASCADE
                                                           ON UPDATE CASCADE,
    UserId    INTEGER     NOT NULL
                          REFERENCES User ( IdUser ) ON DELETE CASCADE
                                                     ON UPDATE CASCADE 
);


-- Table: Category
CREATE TABLE Category ( 
    IdCategory INTEGER        PRIMARY KEY AUTOINCREMENT
                              NOT NULL,
    Name       VARCHAR( 60 )  NOT NULL,
    Url        VARCHAR( 60 )  NOT NULL
                              UNIQUE 
);


-- Table: Project
CREATE TABLE Project ( 
    IdProject        INTEGER           PRIMARY KEY AUTOINCREMENT
                                       NOT NULL,
    Title            VARCHAR( 60 )     NOT NULL,
    ShortDescription VARCHAR( 120 )    NOT NULL,
    LongDescription  TEXT              NOT NULL,
    Story            TEXT              NOT NULL,
    Goal             NUMERIC( 10, 2 )  NOT NULL,
    ImageUrl         TEXT              NOT NULL,
    CategoryId       INTEGER           NOT NULL
                                       REFERENCES Category ( IdCategory ) ON DELETE RESTRICT
                                                                          ON UPDATE CASCADE,
    ManagerId        INTEGER           NOT NULL
                                       REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                                  ON UPDATE CASCADE 
);


-- Table: Pledge
CREATE TABLE Pledge ( 
    IdPledge    INTEGER           PRIMARY KEY AUTOINCREMENT
                                  NOT NULL,
    Description VARCHAR( 60 )     NOT NULL,
    Value       NUMERIC( 10, 2 )  NOT NULL,
    ProjectId   INTEGER           NOT NULL
                                  REFERENCES Project ( IdProject ) ON DELETE CASCADE
                                                                   ON UPDATE CASCADE 
);


-- Table: Reward
CREATE TABLE Reward ( 
    IdReward    INTEGER         PRIMARY KEY AUTOINCREMENT
                                NOT NULL,
    Description VARCHAR( 120 )  NOT NULL,
    ProjectId   INTEGER         NOT NULL
                                REFERENCES Project ( IdProject ) ON DELETE CASCADE
                                                                 ON UPDATE CASCADE 
);


-- Table: OpenProject
CREATE TABLE OpenProject ( 
    ProjectId INTEGER  PRIMARY KEY
                       NOT NULL
                       REFERENCES Project ( IdProject ) ON DELETE CASCADE
                                                        ON UPDATE CASCADE,
    OpenDate  DATETIME NOT NULL 
);


-- Table: Booting
CREATE TABLE Booting ( 
    UserId        INTEGER  NOT NULL
                           REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                      ON UPDATE CASCADE,
    OpenProjectId INTEGER  NOT NULL
                           REFERENCES OpenProject ( ProjectId ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE,
    CardId        INTEGER  REFERENCES Card ( IdCard ) ON DELETE SET NULL
                                                      ON UPDATE CASCADE,
    AddressId     INTEGER  REFERENCES Address ( IdAddress ) ON DELETE SET NULL
                                                            ON UPDATE CASCADE,
    BootingDate   DATETIME NOT NULL,
    PledgeId      INTEGER  NOT NULL
                           REFERENCES Pledge ( IdPledge ) ON DELETE CASCADE
                                                          ON UPDATE CASCADE,
    PRIMARY KEY ( UserId, OpenProjectId )  ON CONFLICT IGNORE,
    FOREIGN KEY ( UserId ) REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                          ON UPDATE CASCADE,
    FOREIGN KEY ( OpenProjectId ) REFERENCES OpenProject ( ProjectId ) ON DELETE CASCADE
                                                                           ON UPDATE CASCADE 
);


-- Table: RewardPledge
CREATE TABLE RewardPledge ( 
    RewardId INTEGER NOT NULL,
    PledgeId INTEGER NOT NULL,
    PRIMARY KEY ( RewardId, PledgeId ),
    UNIQUE ( RewardId, PledgeId ),
    FOREIGN KEY ( RewardId ) REFERENCES Reward ( IdReward ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE,
    FOREIGN KEY ( PledgeId ) REFERENCES Pledge ( IdPledge ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE 
);


-- Table: ClosedProject
CREATE TABLE ClosedProject ( 
    OpenProjectId INTEGER  PRIMARY KEY
                           NOT NULL
                           REFERENCES OpenProject ( ProjectId ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE,
    ClosedDate    DATETIME NOT NULL 
);


-- Table: Credential
CREATE TABLE Credential ( 
    UserId       INTEGER        PRIMARY KEY
                                NOT NULL
                                REFERENCES User ( IdUser ) ON DELETE CASCADE
                                                           ON UPDATE CASCADE,
    PasswordSalt VARCHAR( 22 )  NOT NULL,
    PasswordHash VARCHAR( 64 )  NOT NULL 
);


-- Index: idx_CategoryUrl
CREATE INDEX idx_CategoryUrl ON Category ( 
    Url COLLATE NOCASE ASC 
);


-- Index: idx_ProjectTitle
CREATE INDEX idx_ProjectTitle ON Project ( 
    Title COLLATE NOCASE ASC 
);


-- Index: idx_ProjectDesc
CREATE INDEX idx_ProjectDesc ON Project ( 
    ShortDescription COLLATE NOCASE ASC 
);


-- View: RewardStat
CREATE VIEW RewardStat AS
       SELECT Users.UserId,
              Users.Username,
              Users.Value,
              Users.ProjectId,
              Rewards.RewardDescription,
              Rewards.RewardCount,
              Pledges.PledgeDescription,
              Pledges.PledgeCount
         FROM ( 
           SELECT Pledges.UserId,
                  Pledges.Username,
                  Pledges.ProjectId,
                  SUM( Pledges.Value ) AS Value
             FROM ( 
                   SELECT IdBooting,
                          UserId,
                          IdPledge,
                          ProjectId,
                          Username,
                          Pledge.Description AS PledgeDescription,
                          SUM( Value ) AS Value
                     FROM Booting
                          INNER JOIN User
                                  ON Booting.UserId = User.IdUser
                          INNER JOIN Pledge
                                  ON Booting.PledgeId = Pledge.IdPledge
                    GROUP BY Booting.OpenProjectId,
                             Idpledge,
                             UserId 
               ) 
               AS Pledges
            GROUP BY Pledges.ProjectId,
                     Pledges.UserId 
       ) 
       AS Users
              INNER JOIN ( 
           SELECT UserId,
                  Reward.ProjectId AS ProjectId,
                  Reward.Description AS RewardDescription,
                  COUNT( IdReward ) AS RewardCount
             FROM Booting
                  INNER JOIN RewardPledge
                          ON RewardPledge.PledgeId == Booting.PledgeId
                  INNER JOIN Reward
                          ON Reward.IdReward = RewardPledge.RewardId
            GROUP BY UserId,
                     RewardId 
       ) 
       AS Rewards
                      ON ( Users.UserId = Rewards.UserId ) 
       AND
       ( Users.ProjectId = Rewards.ProjectId ) 
              INNER JOIN ( 
           SELECT PledgeId,
                  UserId,
                  Pledge.Description AS PledgeDescription,
                  COUNT( Booting.PledgeId ) AS PledgeCount,
                  ProjectId
             FROM Booting
                  INNER JOIN Pledge
                          ON Booting.PledgeId = Pledge.IdPledge
            GROUP BY UserId,
                     PledgeId 
       ) 
       AS Pledges
                      ON ( Pledges.UserId == Users.UserId ) 
       AND
       ( Pledges.ProjectId == Users.ProjectId );
;


-- View: PledgeStat
CREATE VIEW PledgeStat AS
       SELECT IdPledge,
              ProjectId,
              Description,
              Value,
              COUNT( UserId ) AS PledgeCount,
              COUNT( UserId ) * Value AS TotalValue
         FROM Pledge
              LEFT JOIN Booting
                     ON Pledge.IdPledge = Booting.PledgeId
        GROUP BY Pledge.IdPledge;
;


-- View: ExpectedRewards
CREATE VIEW ExpectedRewards AS
       SELECT Pledge.ProjectId AS ProjectId,
              Booting.UserId AS UserId,
              Booting.PledgeId AS PledgeId,
              Pledge.Description AS PledgeDescription,
              Pledge.Value AS Value,
              Reward.IdReward AS RewardId,
              Reward.Description AS RewardDescription
         FROM Booting
              INNER JOIN Pledge
                      ON Pledge.IdPledge = Booting.PledgeId
              INNER JOIN RewardPledge
                      ON RewardPledge.PledgeId = Booting.PledgeId
              INNER JOIN Reward
                      ON RewardPledge.RewardId = Reward.IdReward;
;


-- View: ProjectStat
CREATE VIEW ProjectStat AS
       SELECT IdProject,
              Goal,
              CAST ( IFNULL( CAST ( SUM( TotalValue )  AS Float ) / goal * 100, 0 )  AS Integer ) AS Progress,
              MIN( 100, CAST ( IFNULL( CAST ( SUM( TotalValue )  AS Float ) / goal * 100, 0 )  AS Integer )  ) AS LimitedProgress,
              IFNULL( SUM( TotalValue ) >= Goal, 0 ) AS Funded,
              IFNULL( SUM( TotalValue ) , 0 ) AS TotalValue,
              IFNULL( SUM( PledgeCount ) , 0 ) AS Bootings,
              Goal - IFNULL( SUM( TotalValue ) , 0 )  Remaining
         FROM Project
              LEFT OUTER JOIN PledgeStat
                           ON Project.IdProject == PledgeStat.ProjectId
        GROUP BY IdProject;
;

