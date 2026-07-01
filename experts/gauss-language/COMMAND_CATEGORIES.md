# GAUSS Command Categories

This document provides a native GAUSS command inventory organized by official command category. It is intended to help GAUSS AI agents identify candidate built-in commands before writing custom manual implementations.

The lists below are derived from the official GAUSS documentation command category index and category files. Category membership helps identify possible native commands, but exact syntax, arguments, return values, and version behavior still require checking the command-specific documentation.

## Category Summary

| Category | Source file | Notes |
| --- | --- | --- |
| Data types | `cc/data-types.rst` | DataFrames, matrices, arrays, strings, dates, and related type utilities. |
| Data Import and Export | `cc/data-import-and-export.rst` | File, spreadsheet, database, HDF5, and data I/O commands. |
| Data cleaning | `cc/data-cleaning.rst` | Selection, sorting, joining, missing values, reshaping, and categorical utilities. |
| Descriptive statistics and computation | `cc/descriptive-statistics.rst` | Summary statistics, frequency tables, tests, and related computations. |
| Estimation methods | `cc/estimation-methods.rst` | Modeling, standard errors, regression, tests, and decomposition/solver commands. |
| Graphics | `cc/graphics.rst` | Plot creation, plot additions, layout, styling, legends, and export. |
| Optimization and Solution | `cc/optimization-and-solution.rst` | Optimization and equation-solving commands. |
| Mathematical functions | `cc/mathematical-functions.rst` | Math, linear algebra, decompositions, regression, transforms, and numerical utilities. |
| Operators | `cc/operators.rst` | Arithmetic, string, relational, logical, and other operators. |
| Panel Data | `cc/panel-data.rst` | Panel data checks, transformations, summaries, and related DataFrame operations. |
| Statistical distributions and sampling | `cc/statistical-distributions.rst` | CDF, PDF, random number, sampling, and distribution utilities. |
| Time and Date | `cc/time-and-date.rst` | Date/time conversion, parsing, formatting, components, and sequences. |
| String handling | `cc/string-handling.rst` | String conversion, search, split, trim, replacement, and token utilities. |
| Programming | `cc/programming.rst` | Control flow, procedures, debugging, output, dynamic arguments, and execution. |
| Multithreading and parallelization | `cc/parallelization.rst` | Thread commands. |
| Web | `cc/web.rst` | Web data source commands. |
| Workspace, files, folders and paths | `cc/workspace-file-folder-os.rst` | Workspace, filesystem, source path, and environment commands. |

## Data Types

Commands: `aconcat`, `aeye`, `amax`, `amean`, `amin`, `areshape`, `arrayalloc`, `arrayindex`, `arrayinit`, `arraytomat`, `asdate`, `asdf`, `asmatrix`, `astd`, `asum`, `atranspose`, `cols`, `colsf`, `complex`, `dfappend`, `dfname`, `dftype`, `diag`, `diagrv`, `dropcategories`, `dropunusedcategories`, `dtdayname`, `dtdayofmonth`, `dtdayofweek`, `dtdayofyear`, `dthour`, `dtminute`, `dtmonth`, `dtmonthname`, `dtquarter`, `dtsecond`, `dtweek`, `dtyear`, `endswith`, `eye`, `getarray`, `getcategories`, `getcoldateformats`, `getcollabels`, `getcolnames`, `getcoltypes`, `getdims`, `getmatrix`, `getmatrix4d`, `getorders`, `getscalar3d`, `getscalar4d`, `hasimag`, `hasmetadata`, `imag`, `iscplx`, `loopnextindex`, `matalloc`, `matinit`, `mattoarray`, `maxc`, `minc`, `nextindex`, `ones`, `previousindex`, `putarray`, `real`, `recodecatlabels`, `reordercatlabels`, `rows`, `rowsf`, `setbasecat`, `setcoldateformats`, `setcolmetadata`, `setcolnames`, `singleindex`, `squeeze`, `startswith`, `walkindex`, `zeros`.

Combined official references not split here: `lowmatlowmat1`, `upmatupmat1`.

## Data Import and Export

Commands: `close`, `closeall`, `csvreadm`, `csvreadsa`, `csvwritem`, `datacreate`, `dataopen`, `dbadddatabase`, `dbclose`, `dbcommit`, `dbcreatequery`, `dbexecqueries`, `dbexecquery`, `dbgetconnectoptions`, `dbgetdatabasename`, `dbgetdrivername`, `dbgetdrivers`, `dbgethostname`, `dbgetlasterrornum`, `dbgetlasterrortext`, `dbgetnumericalprecpolicy`, `dbgetpassword`, `dbgetport`, `dbgetprimaryindex`, `dbgettableheaders`, `dbgettables`, `dbhasfeature`, `dbisdriveravailable`, `dbisopen`, `dbisopenerror`, `dbisvalid`, `dbopen`, `dbquerybindvalue`, `dbqueryclear`, `dbquerycols`, `dbqueryexecprepared`, `dbqueryfetchallm`, `dbqueryfetchallsa`, `dbqueryfetchonem`, `dbqueryfetchonesa`, `dbqueryfinish`, `dbquerygetboundvalue`, `dbquerygetboundvalues`, `dbquerygetfield`, `dbquerygetlasterrornum`, `dbquerygetlasterrortext`, `dbquerygetlastinsertid`, `dbquerygetlastquery`, `dbquerygetnumrowsaffected`, `dbquerygetposition`, `dbqueryisactive`, `dbqueryisforwardonly`, `dbqueryisnull`, `dbqueryisselect`, `dbqueryisvalid`, `dbqueryprepare`, `dbqueryrows`, `dbqueryseek`, `dbqueryseekfirst`, `dbqueryseeklast`, `dbqueryseeknext`, `dbqueryseekprevious`, `dbquerysetforwardonly`, `dbremovedatabase`, `dbrollback`, `dbsetconnectoptions`, `dbsetdatabasename`, `dbsethostname`, `dbsetnumericalprecpolicy`, `dbsetpassword`, `dbsetport`, `dbtransaction`, `eof`, `fcheckerr`, `fclearerr`, `fflush`, `fgets`, `fgetsa`, `fgetsat`, `fgetst`, `fopen`, `fputs`, `fputst`, `fseek`, `fstrerror`, `ftell`, `getf`, `getheaders`, `getnr`, `getnrmt`, `h5create`, `h5open`, `h5read`, `h5readattribute`, `h5write`, `loadd`, `putf`, `readr`, `saved`, `seekr`, `tempname`, `typef`, `writer`, `xlsgetsheetcount`, `xlsgetsheetsize`, `xlsgetsheettypes`, `xlsmakerange`, `xlsreadm`, `xlsreadsa`, `xlswrite`.

## Data Cleaning

Commands: `between`, `code`, `cols`, `contains`, `counts`, `countwts`, `delcols`, `delif`, `delrows`, `dfappend`, `dflonger`, `dfwider`, `diag`, `diagrv`, `dropduplicates`, `dummy`, `dummybr`, `dummydn`, `getcollabels`, `getdims`, `getduplicates`, `getmatrix`, `getorders`, `head`, `impute`, `indexcat`, `indnv`, `innerjoin`, `insertcols`, `intrsect`, `isempty`, `isinfnanmiss`, `ismember`, `ismiss`, `isrowunique`, `isunique`, `lagn`, `lagtrim`, `maxindc`, `maxv`, `minindc`, `minv`, `missex`, `missmissrv`, `msym`, `order`, `outerjoin`, `packr`, `pddiff`, `pdlag`, `reclassify`, `reclassifycuts`, `recodecatlabels`, `reordercatlabels`, `rescale`, `reshape`, `rev`, `rotater`, `rowcontains`, `rows`, `scalmiss`, `selif`, `setbasecat`, `setdif`, `shiftc`, `shiftr`, `sortc`, `sortmc`, `strreplace`, `strtof`, `strtrim`, `strtriml`, `strtrimr`, `submat`, `subscat`, `substute`, `subvec`, `tail`, `trimr`, `union`, `uniqindx`, `unique`, `vech`, `where`, `xpnd`.

Combined official references not split here: `sortindsortindc`, `sortrsortrc`, `vecvecr`.

## Descriptive Statistics and Computation

Commands: `aggregate`, `contingency`, `cumprodc`, `cumsumc`, `dstatmt`, `frequency`, `jarquebera`, `kurtosis`, `maxc`, `maxindc`, `meanc`, `median`, `minc`, `minindc`, `modec`, `mvntest`, `pdsummary`, `prodc`, `prodr`, `quantile`, `shapirowilk`, `skew`, `stdc`, `sumc`, `sumr`, `tabulate`, `vcmvcx`.

## Estimation Methods

Commands: `clusterse`, `fgls`, `glm`, `gmmfit`, `gmmfitiv`, `hacse`, `kerneldensity`, `ldlp`, `ldlsol`, `lu`, `lusol`, `olsmt`, `olsqr`, `olsqr2`, `qfitslopetest`, `quantilefit`, `quantilefitloc`, `robustse`, `solpd`, `ttest`, `waltest`.

## Graphics

Commands: `annotationgetdefaults`, `annotationsetbkd`, `annotationsetfont`, `annotationsetlinecolor`, `annotationsetlinepen`, `annotationsetlinestyle`, `annotationsetlinethickness`, `annotationsettextalign`, `blendcolorpalette`, `getcolorpalette`, `gethslpalette`, `gethsluvpalette`, `listcolorpalettes`, `plotacf`, `plotaddarea`, `plotaddarrow`, `plotaddbar`, `plotaddbarh`, `plotaddbox`, `plotadderrorbar`, `plotaddhbar`, `plotaddhist`, `plotaddhistf`, `plotaddhistp`, `plotaddhline`, `plotaddpolar`, `plotaddscatter`, `plotaddshape`, `plotaddsurface`, `plotaddtextbox`, `plotaddts`, `plotaddtshf`, `plotaddvbar`, `plotaddvline`, `plotaddxy`, `plotaddxyfill`, `plotarea`, `plotbar`, `plotbarh`, `plotbox`, `plotcanvassize`, `plotcdfempirical`, `plotclearlayout`, `plotcloseall`, `plotcontour`, `plotcustomlayout`, `plotfreq`, `plotgetdefaults`, `plothist`, `plothistf`, `plothistp`, `plotlayout`, `plotloglog`, `plotlogx`, `plotlogy`, `plotopenwindow`, `plotpacf`, `plotpolar`, `plotsave`, `plotscatter`, `plotsetactivex`, `plotsetactivey`, `plotsetaxespen`, `plotsetbarwidth`, `plotsetbkdcolor`, `plotsetboxwidth`, `plotsetcolormap`, `plotsetcontourlabels`, `plotsetfill`, `plotsetfonts`, `plotsetgridpen`, `plotsetjitterrange`, `plotsetlegend`, `plotsetlegendbkd`, `plotsetlegendborder`, `plotsetlegendfont`, `plotsetlegendtitle`, `plotsetlinepen`, `plotsetlinesymbol`, `plotsetmissgap`, `plotsetnewwindow`, `plotsetoutlineenabled`, `plotsettextinterpreter`, `plotsetticlabelfont`, `plotsetticposition`, `plotsettitle`, `plotsetwhichxaxis`, `plotsetwhichyaxis`, `plotsetxgridpen`, `plotsetxlabel`, `plotsetxminorticcount`, `plotsetxpen`, `plotsetxrange`, `plotsetxticinterval`, `plotsetxticlabel`, `plotsetxticposition`, `plotsetygridpen`, `plotsetylabel`, `plotsetyminorticcount`, `plotsetypen`, `plotsetyrange`, `plotsetyticinterval`, `plotsetyticlabel`, `plotsetyticposition`, `plotsetzlabel`, `plotsetzlevels`, `plotsurface`, `plotts`, `plottshf`, `plottslog`, `plotxy`, `plotxyfill`.

## Optimization and Solution

Commands: `eqsolve`, `eqsolvemt`, `minimize`, `minimizecontrolcreate`, `qnewton`, `qnewtonmt`, `qprog`, `qprogmt`, `sqpsolve`, `sqpsolvemt`.

## Mathematical Functions

Commands: `abs`, `acf`, `arccos`, `arcsin`, `astd`, `astds`, `atan`, `atan2`, `balance`, `band`, `bandchol`, `bandcholsol`, `bandltsol`, `bandrv`, `bandsolpd`, `base10`, `besselj`, `besselk`, `bessely`, `beta`, `blockdiag`, `boxcox`, `ceil`, `chibarsquare`, `chol`, `choldn`, `cholsol`, `cholup`, `clusterse`, `combinate`, `combinated`, `cond`, `conscore`, `conv`, `cos`, `cosh`, `crossprd`, `crout`, `croutp`, `curve`, `design`, `det`, `detl`, `dfft`, `dffti`, `digamma`, `dot`, `dstatmt`, `dwstat`, `eig`, `eigh`, `eighv`, `eigv`, `exp`, `fft`, `ffti`, `fftm`, `fftmi`, `fftn`, `fix`, `floor`, `fmod`, `gamma`, `gammacplx`, `gammaii`, `gdadstat`, `gdadstatmat`, `glm`, `gmmfit`, `gmmfitiv`, `gradmtm`, `gradmtt`, `gradmttm`, `hess`, `hessmtg`, `hessmtgw`, `hessmtm`, `hessmtmw`, `hessmtt`, `hessmttg`, `hessmttgw`, `hessmttm`, `hessmtw`, `integrate1d`, `intgrat2`, `intgrat3`, `intquad1`, `intquad2`, `intquad3`, `intsimp`, `invswp`, `lapeighb`, `lapeighi`, `lapeighvb`, `lapeighvi`, `lapgeig`, `lapgeigh`, `lapgeighv`, `lapgeigv`, `lapgschur`, `lapgsvdcst`, `lapgsvds`, `lapgsvdst`, `ldl`, `ldlp`, `ldlsol`, `ln`, `lnfact`, `lngamma`, `loess`, `loessmt`, `log`, `lu`, `lusol`, `machepsilon`, `mbesseli`, `meanc`, `median`, `moment`, `momentd`, `movingave`, `movingaveexpwgt`, `movingavewgt`, `norm`, `null`, `null1`, `numcombinations`, `ols`, `olsmt`, `olsqr`, `olsqr2`, `olsqrmt`, `orth`, `pacf`, `pi`, `pinv`, `pinvmt`, `polychar`, `polyeval`, `polygamma`, `polyint`, `polymake`, `polymat`, `polymult`, `polyroot`, `powerm`, `princomp`, `psi`, `qqr`, `qqre`, `qqrep`, `qr`, `qre`, `qrep`, `qrsol`, `qrtsol`, `qtyr`, `qtyre`, `qtyrep`, `quantile`, `quantiled`, `quantilefit`, `quantilefitloc`, `qyr`, `qyre`, `qyrep`, `qz`, `rank`, `recserar`, `recsercp`, `recserrc`, `recservar`, `rfft`, `rffti`, `rfftip`, `rfftn`, `rfftnp`, `rfftp`, `robustse`, `round`, `rref`, `schtoc`, `schur`, `seqadt`, `seqaposix`, `seqaseqm`, `sin`, `sinh`, `solpd`, `spline`, `sqrt`, `stdc`, `svd`, `svd1`, `svd2`, `svdcusv`, `svds`, `svdusv`, `sylvester`, `tan`, `tanh`, `tocart`, `toeplitz`, `topolar`, `tracem`, `trigamma`, `trunc`, `varmall`, `varmares`, `vcmvcx`, `zeta`.

Combined official references not split here: `corrmcorrvccorrx`, `dotfeqdotfgedotfgtdotfledotfltdotfne`, `dotfeqmtdotfgemtdotfgtmtdotflemtdotfltmtdotfnemt`, `feqfgefgtflefltfne`, `feqmtfgemtfgtmtflemtfltmtfnemt`, `gradpgradcplx`, `hessphesscplx`, `invinvpd`.

## Operators

Operators and keywords: `+`, `-`, `*`, `.*`, `.*.`, `/`, `./`, `.^`, `!`, `%`, `'`, `.'`, `=`, `:`, `|`, `~`, `$+`, `$|`, `$~`, `.==`, `==`, `!=`, `.!=`, `>`, `.>`, `.>=`, `>=`, `<`, `.<`, `.<=`, `<=`, `not`, `and`, `or`, `xor`, `eqv`, `&`, `^`.

## Panel Data

Commands: `aggregate`, `between`, `contains`, `counts`, `countwts`, `dfappend`, `dflonger`, `dfwider`, `dropduplicates`, `frequency`, `getcollabels`, `getduplicates`, `indexcat`, `indnv`, `innerjoin`, `insertcols`, `isempty`, `isinfnanmiss`, `ismember`, `ismiss`, `isrowunique`, `isunique`, `maxindc`, `minindc`, `missex`, `missmissrv`, `msym`, `outerjoin`, `packr`, `pdallbalanced`, `pdallconsecutive`, `pdbalance`, `pddiff`, `pdisbalanced`, `pdisconsecutive`, `pdlag`, `pdsize`, `pdsort`, `pdsummary`, `pdtimespans`, `plotfreq`, `reclassify`, `reclassifycuts`, `recodecatlabels`, `reordercatlabels`, `rowcontains`, `scalmiss`, `setbasecat`, `sortmc`, `strreplace`, `strtof`, `strtrim`, `strtriml`, `strtrimr`, `tabulate`, `where`.

## Multithreading and Parallelization

Commands: `threadbegin`, `threadend`, `threadfor`, `threadjoin`, `threadstat`.

## Programming

Commands: `break`, `call`, `changedir`, `compile`, `con_`, `cons`, `continue`, `debug`, `dynargscount`, `dynargsget`, `dynargstypes`, `end`, `endp`, `error`, `errorlog`, `errorlogat`, `fn`, `for`, `head`, `if`, `key`, `keyav`, `keyw`, `keyword`, `local`, `output`, `pause`, `print`, `proc`, `retp`, `run`, `scalerr`, `sleep`, `sprintf`, `stop`, `system`, `tail`, `trace`, `trap`, `trapchk`, `warninglog`, `warninglogat`.

Combined official references not split here: `dowhiledountil`, `linesonlinesoff`, `waitwaitc`.

## Statistical Distributions and Sampling

Commands: `cdfbeta`, `cdfbetainv`, `cdfbinomial`, `cdfbinomialinv`, `cdfbvn`, `cdfbvn2`, `cdfbvn2e`, `cdfcauchy`, `cdfcauchyinv`, `cdfchic`, `cdfchii`, `cdfchinc`, `cdfempirical`, `cdfexp`, `cdfexpinv`, `cdffc`, `cdffnc`, `cdffncinv`, `cdfgam`, `cdfgenpareto`, `cdfhypergeo`, `cdflaplace`, `cdflaplaceinv`, `cdflognorm`, `cdfmvn`, `cdfmvn2e`, `cdfmvnce`, `cdfmvne`, `cdfmvt2e`, `cdfmvtce`, `cdfmvte`, `cdfn2`, `cdfnegbinomial`, `cdfnegbinomialinv`, `cdfni`, `cdfpoisson`, `cdfpoissoninv`, `cdfrayleigh`, `cdfrayleighinv`, `cdftc`, `cdftci`, `cdftnc`, `cdftruncnorm`, `cdftvn`, `cdfweibull`, `cdfweibullinv`, `lncdfbvn`, `lncdfbvn2`, `lncdfmvn`, `lncdfn`, `lncdfn2`, `lncdfnc`, `lnpdfmvn`, `lnpdfmvt`, `lnpdfn`, `lnpdft`, `pdfbinomial`, `pdfcauchy`, `pdfexp`, `pdfgenpareto`, `pdfhypergeo`, `pdflaplace`, `pdflogistic`, `pdflognorm`, `pdfn`, `pdfpoisson`, `pdfrayleigh`, `pdftruncnorm`, `pdfweibull`, `pdfwishartinv`, `rndbernoulli`, `rndbeta`, `rndbinomial`, `rndcauchy`, `rndchisquare`, `rndcreatestate`, `rndexp`, `rndgamma`, `rndgeo`, `rndgumbel`, `rndhypergeo`, `rndi`, `rndkmvm`, `rndlaplace`, `rndlognorm`, `rndmvn`, `rndmvt`, `rndn`, `rndnegbinomial`, `rndpoisson`, `rndrayleigh`, `rndseed`, `rndstateskip`, `rndu`, `rndweibull`, `rndwishart`, `rndwishartinv`, `sampledata`.

Combined official references not split here: `cdfncdfnc`, `erferfc`, `erfcplxerfccplx`.

## String Handling

Commands: `chrs`, `ftos`, `ftostrc`, `isstring`, `itos`, `lower`, `ntos`, `stof`, `strcombine`, `strindx`, `strjoin`, `strlen`, `strput`, `strreplace`, `strrindx`, `strsect`, `strsplit`, `strsplitpad`, `strtof`, `strtofcplx`, `strtrim`, `strtriml`, `strtrimr`, `strtrunc`, `strtruncl`, `strtruncpad`, `strtruncr`, `token`, `upper`, `vals`.

## Time and Date

Commands: `asdate`, `date`, `datestr`, `datestring`, `datestrymd`, `dayinyr`, `dayofweek`, `dtdate`, `dtday`, `dtdayname`, `dtdayofmonth`, `dtdayofweek`, `dtdayofyear`, `dthour`, `dtminute`, `dtmonth`, `dtmonthname`, `dtquarter`, `dtsecond`, `dttime`, `dttodtv`, `dttoposix`, `dttostr`, `dttostrc`, `dttoutc`, `dtvnormal`, `dtvtodt`, `dtvtoutc`, `dtweek`, `dtyear`, `etdays`, `ethsec`, `etstr`, `getcoldateformats`, `hsec`, `posixtostrc`, `seqadt`, `seqaposix`, `setcoldateformats`, `strctodt`, `strctoposix`, `strtodt`, `time`, `timedeltadt`, `timedeltaposix`, `timediffdt`, `timediffposix`, `timedt`, `timestr`, `timeutc`, `todaydt`, `utctodt`, `utctodtv`.

## Web

Commands: `dbnomics_series`, `dbnomics_set`, `fred_load`, `fred_search`, `fred_set`.

## Workspace, Files, Folders and Paths

Commands: `_file_dir`, `cdir`, `changedir`, `chdir`, `clear`, `delete`, `deletefile`, `envget`, `exec`, `getgausshome`, `includedir`, `new`, `resetsourcepaths`, `show`.

## Extraction Notes

- The command category index was read from `command-reference.rst`; category entries were taken from its command-category toctree.
- Category command names were extracted from official `:doc:` references in the corresponding `cc/*.rst` files.
- Some official category files contain combined documentation targets for groups of related commands, such as `sortindsortindc` or `invinvpd`. Those targets are preserved as combined references rather than split into separate commands by inference.
- The `Operators` category is represented as operators and logical keywords because the source file documents symbols and operator keywords rather than procedure names.
